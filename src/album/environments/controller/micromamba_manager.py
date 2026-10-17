"""Module for handling micromamba environments."""
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Mapping, Optional, Union

from album.runner.album_logging import get_active_logger

from album.environments.controller.package_manager import PackageManager
from album.environments.model.environment_default_values import EnvironmentDefaultValues

# TODO: Still has the conda executable of the CondaManager parent class. I don' like that, maybe create an extra package
#  manager class from which every Manager(conda/mamba/micromamba) inherits


class MicromambaManager(PackageManager):
    """Class for handling micromamba environments.

    The micromamba class manages the environments a solution is supposed to run in. It provides all features necessary
    for environment creation, deletion, dependency installation, etc.

    Notes:
        An installed "micromamba" program must be available and callable at the .album/micromamba directory.

    """

    # Prefix of the temporary directory that holds the private process registry of one "micromamba run"
    _private_proc_dir_prefix = "album-micromamba-run-"
    # A private registry without a running process that was last modified longer ago is a leftover
    _leftover_private_proc_dir_age_seconds = 3600

    def __init__(self, micromamba_executable: str, base_env_path: Path):
        super().__init__(micromamba_executable, "micromamba", base_env_path)

    def get_active_environment_name(self) -> str:
        environment_info = self.get_info()
        env_name = environment_info["environment"]
        env_name = env_name.rstrip(" (active)")
        return env_name

    def get_active_environment_path(self) -> str:
        # todo: seems not to work within pycharm, but works in the terminal. Investigate!
        environment_info = self.get_info()
        path = environment_info["env location"]
        return path

    def _get_env_create_args(
        self, env_file: tempfile.TemporaryFile, env_prefix: str
    ) -> List[str]:
        subprocess_args = [
            self.get_install_environment_executable(),
            "create",
            "-y",
            "--file",
            env_file.name,
            "-p",
            env_prefix,
        ]
        return subprocess_args

    def _get_run_script_args(
        self,
        environment_path: Union[Path, tempfile.TemporaryFile],
        script_full_path: str,
    ) -> List[str]:
        if sys.platform == "win32" or sys.platform == "cygwin":
            # NOTE: WHEN USING 'CONDA RUN' THE CORRECT ENVIRONMENT GETS TEMPORARY ACTIVATED,
            # BUT THE PATH POINTS TO THE WRONG PYTHON (conda base folder python) BECAUSE THE CONDA BASE PATH
            # COMES FIRST IN ENVIRONMENT VARIABLE "%PATH%". THUS, FULL PATH IS NECESSARY TO CALL
            # THE CORRECT PYTHON OR PIP! ToDo: keep track of this!
            subprocess_args = [
                self.get_install_environment_executable(),
                "run",
                "--prefix",
                os.path.normpath(environment_path),
                os.path.normpath(Path(environment_path).joinpath("python")),
                "-u",
                os.path.normpath(script_full_path),
            ]
        else:
            subprocess_args = [
                self.get_install_environment_executable(),
                "run",
                "--prefix",
                os.path.normpath(environment_path),
                "python",
                "-u",
                os.path.normpath(script_full_path),
            ]
        return subprocess_args

    def _run_script_process(
        self,
        subprocess_args: List[str],
        environment_variables: Union[
            Mapping,
            None,
        ],
        pipe_output: bool,
    ) -> None:
        if not self._use_private_proc_dir():
            super()._run_script_process(
                subprocess_args, environment_variables, pipe_output
            )
            return

        # "micromamba run" registers every process in <XDG_CACHE_HOME or ~/.cache>/mamba/proc, a registry shared by
        # all runs of the user and guarded by a file lock. Parallel runs (e.g. HPC jobs sharing a home directory)
        # queue on that lock ("Cannot lock '~/.cache/mamba/proc'") and occasionally fail reading another run's
        # half-written entry (album#227). micromamba (checked for 2.5.0) uses XDG_CACHE_HOME for nothing but this
        # registry, so every run gets a private, temporary one. "env" hands the caller's XDG_CACHE_HOME (or its
        # absence) back to the solution's command, so pip, pooch, torch etc. keep using their usual caches.
        command_start = self._get_run_command_start(subprocess_args)
        if command_start is None:
            get_active_logger().warning(
                "Unexpected micromamba call, using the shared process registry: %s"
                % " ".join(subprocess_args)
            )
            super()._run_script_process(
                subprocess_args, environment_variables, pipe_output
            )
            return
        process_env = dict(
            os.environ if environment_variables is None else environment_variables
        )
        caller_cache_home = process_env.get("XDG_CACHE_HOME")
        if caller_cache_home is None:
            restore_cache_home = ["env", "-u", "XDG_CACHE_HOME"]
        else:
            restore_cache_home = ["env", "XDG_CACHE_HOME=%s" % caller_cache_home]
        args = (
            subprocess_args[:command_start]
            + restore_cache_home
            + subprocess_args[command_start:]
        )

        proc_cache_dir = tempfile.mkdtemp(prefix=self._private_proc_dir_prefix)
        get_active_logger().debug(
            "Using private micromamba process registry in %s" % proc_cache_dir
        )
        process_env["XDG_CACHE_HOME"] = proc_cache_dir
        try:
            self._remove_leftover_private_proc_dirs(proc_cache_dir)
            super()._run_script_process(args, process_env, pipe_output)
        finally:
            shutil.rmtree(proc_cache_dir, ignore_errors=True)

    @staticmethod
    def _get_run_command_start(subprocess_args: List[str]) -> Optional[int]:
        """Return where the solution's command starts in the call built by _get_run_script_args.

        The call is [<micromamba>, "run", "--prefix", <environment>, <command>...]. Returns None for any other
        layout, so the command is never wrapped at the wrong position.
        """
        if len(subprocess_args) > 4 and subprocess_args[1:3] == ["run", "--prefix"]:
            return 4
        return None

    @classmethod
    def _remove_leftover_private_proc_dirs(cls, own_proc_cache_dir: str) -> None:
        """Remove the private process registries that interrupted runs left behind.

        The cleanup in _run_script_process does not run when album is terminated (SIGTERM from a job scheduler,
        SIGKILL). On Ctrl-C it runs while micromamba is still exiting, and micromamba then re-creates
        mamba/proc/proc.lock. A registry is removed only if it belongs to the current user, holds no
        mamba/proc/<pid>.json (micromamba keeps that file while it runs) and was not modified for an hour.
        """
        parent = os.path.dirname(own_proc_cache_dir)
        own_name = os.path.basename(own_proc_cache_dir)
        modified_before = time.time() - cls._leftover_private_proc_dir_age_seconds
        try:
            owner = os.stat(own_proc_cache_dir).st_uid
            with os.scandir(parent) as entries:
                candidates = [
                    entry
                    for entry in entries
                    if entry.name.startswith(cls._private_proc_dir_prefix)
                    and entry.name != own_name
                ]
        except OSError:
            return
        for entry in candidates:
            try:
                if (
                    not entry.is_dir(follow_symlinks=False)
                    or entry.stat(follow_symlinks=False).st_uid != owner
                    or not cls._is_leftover_private_proc_dir(
                        entry.path, modified_before
                    )
                ):
                    continue
            except OSError:
                continue
            get_active_logger().debug(
                "Removing leftover micromamba process registry %s" % entry.path
            )
            shutil.rmtree(entry.path, ignore_errors=True)

    @staticmethod
    def _is_leftover_private_proc_dir(path: str, modified_before: float) -> bool:
        proc_dir = os.path.join(path, "mamba", "proc")
        # a run that ended a moment ago has just modified mamba/proc (deleting its <pid>.json)
        for directory in (path, os.path.dirname(proc_dir), proc_dir):
            if not os.path.isdir(directory):
                break
            if os.stat(directory).st_mtime > modified_before:
                return False
        if not os.path.isdir(proc_dir):
            return True
        return not any(name.endswith(".json") for name in os.listdir(proc_dir))

    @staticmethod
    def _use_private_proc_dir() -> bool:
        if sys.platform == "win32" or sys.platform == "cygwin":
            # micromamba neither locks nor writes its process registry on Windows
            return False
        setting = os.getenv(
            EnvironmentDefaultValues.micromamba_run_private_proc_dir_env_name.value, ""
        )
        return setting.strip().lower() not in ("0", "false", "no", "off")

    def _get_remove_env_args(self, path: str) -> List[str]:
        subprocess_args = [
            self.get_install_environment_executable(),
            "remove",
            "-y",
            "-q",
            "-p",
            os.path.normpath(path),
            "--all",
        ]
        return subprocess_args

    def _get_pypi_list_args(self, env_prefix: str) -> List[str]:
        subprocess_args = [
            self.get_install_environment_executable(),
            "run",
            "--prefix",
            os.path.normpath(env_prefix),
            self._get_pip_exe(env_prefix),
            "list",
            "--format=json",
        ]
        return subprocess_args

    def _get_base_install_package_args(
        self,
        package_name: str,
        version: Optional[str] = None,
        channel: str = "conda-forge",
    ) -> List[str]:
        pkg = package_name + (f"=={version}" if version else "")
        subprocess_args = [
            self.get_install_environment_executable(),
            "install",
            "-y",
            "-c",
            channel,
            "-p",
            os.path.normpath(self.get_base_environment_path()),
            pkg,
        ]
        return subprocess_args

    def _get_base_env_key(self) -> str:
        return "base environment"
