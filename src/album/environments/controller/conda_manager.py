import os
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Union

from album.runner import album_logging

from album.environments.controller.package_manager import PackageManager

module_logger = album_logging.get_active_logger


class CondaManager(PackageManager):
    """Class for handling conda environments.

    The conda class manages the environments a solution is supposed to run in. It provides all features necessary for
    environment creation, deletion, dependency installation, etc.

    Notes:
        An installed "conda" program must be available and callable via commandline or powershell.

    """

    def __init__(
        self,
        install_executable: str,
        base_env_path: Path,
        package_manager_name: Optional[str] = "conda",
    ):
        assert package_manager_name is not None, "Package manager name must be set!"

        super().__init__(install_executable, package_manager_name, base_env_path)

    def get_active_environment_name(self) -> str:
        environment_info = self.get_info()
        return environment_info["active_prefix_name"]

    def get_active_environment_path(self) -> str:
        environment_info = self.get_info()
        return environment_info["active_prefix"]

    def _get_env_create_args(
        self, env_file: tempfile.TemporaryFile, env_prefix: str
    ) -> List[str]:
        subprocess_args = [
            self.get_install_environment_executable(),
            "env",
            "create",
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
                "--no-capture-output",
                "--prefix",
                os.path.normpath(environment_path),
                os.path.normpath(Path(environment_path).joinpath("python")),
                os.path.normpath(script_full_path),
            ]
        else:
            subprocess_args = [
                self.get_install_environment_executable(),
                "run",
                "--no-capture-output",
                "--prefix",
                os.path.normpath(environment_path),
                "python",
                "-u",
                os.path.normpath(script_full_path),
            ]
        return subprocess_args

    def _get_remove_env_args(self, path: str) -> List[str]:
        subprocess_args = [
            self.get_install_environment_executable(),
            "env",
            "remove",
            "-y",
            "-q",
            "-p",
            os.path.normpath(str(path)),
        ]
        return subprocess_args

    def _get_pypi_list_args(self, env_prefix: str) -> List[str]:
        subprocess_args = [
            self.get_install_environment_executable(),
            "run",
            "--no-capture-output",
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
            "-c " + channel,
            "-p",
            os.path.normpath(self.get_base_environment_path()),
            pkg,
        ]
        return subprocess_args

    def _get_base_env_key(self) -> str:
        return "conda_prefix"
