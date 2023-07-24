from album.environments.controller.conda_manager import CondaManager
from album.runner import album_logging

module_logger = album_logging.get_active_logger
import os
import sys
from pathlib import Path


# TODO: Still has the conda executable of the CondaManager parent class. I don' like that, maybe create an extra package
#  manager class from which every Manager(conda/mamba/micromamba) inherits


class MicromambaManager(CondaManager):
    """Class for handling micromamba environments.

    The micromamba class manages the environments a solution is supposed to run in. It provides all features necessary
    for environment creation, deletion, dependency installation, etc.

    Notes:
        An installed \"micromamba\" program must be available and callable at the .album/micromamba directory.

    """

    def __init__(self, micromamba_executable, base_env_path):
        super().__init__(None, base_env_path)
        self._micromamba_executable = micromamba_executable

    def _get_install_environment_executable(self):
        return self._micromamba_executable

    def get_active_environment_name(self):
        """Returns the environment from the active album."""
        environment_info = self.get_info()
        env_name = environment_info["environment"]
        env_name = env_name.rstrip(" (active)")
        return env_name

    def get_active_environment_path(self):
        """Returns the environment for the active album."""
        environment_info = self.get_info()
        return environment_info["env location"]

    def _get_env_create_args(self, env_file, env_prefix):
        subprocess_args = [
            self._get_install_environment_executable(),
            "create",
            "-y",
            "--file",
            env_file.name,
            "-p",
            env_prefix,
        ]
        return subprocess_args

    def _get_run_script_args(self, environment_path, script_full_path):
        if sys.platform == "win32" or sys.platform == "cygwin":
            # NOTE: WHEN USING 'CONDA RUN' THE CORRECT ENVIRONMENT GETS TEMPORARY ACTIVATED,
            # BUT THE PATH POINTS TO THE WRONG PYTHON (conda base folder python) BECAUSE THE CONDA BASE PATH
            # COMES FIRST IN ENVIRONMENT VARIABLE "%PATH%". THUS, FULL PATH IS NECESSARY TO CALL
            # THE CORRECT PYTHON OR PIP! ToDo: keep track of this!
            subprocess_args = [
                self._micromamba_executable,
                "run",
                "--prefix",
                os.path.normpath(environment_path),
                os.path.normpath(Path(environment_path).joinpath("python")),
                os.path.normpath(script_full_path),
            ]
        else:
            subprocess_args = [
                self._micromamba_executable,
                "run",
                "--prefix",
                os.path.normpath(environment_path),
                "python",
                "-u",
                os.path.normpath(script_full_path),
            ]
        return subprocess_args

    def _get_remove_env_args(self, path):
        subprocess_args = [
            self._get_install_environment_executable(),
            "remove",
            "-y",
            "-q",
            "-p",
            os.path.normpath(path),
            "--all",
        ]
        return subprocess_args
