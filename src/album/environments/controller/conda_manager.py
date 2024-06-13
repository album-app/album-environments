import os
import sys
from pathlib import Path
from typing import List, Optional

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
        package_manager_name: Optional[str] = "conda",
        base_env_path: Optional[Path] = None,
    ):
        super().__init__(install_executable, package_manager_name, base_env_path)

    def get_active_environment_name(self):
        environment_info = self.get_info()
        return environment_info["active_prefix_name"]

    def get_active_environment_path(self):
        environment_info = self.get_info()
        return environment_info["active_prefix"]

    def _get_env_create_args(self, env_file, env_prefix) -> List[str]:
        subprocess_args = [
            self.get_install_environment_executable(),
            "env",
            "create",
            "--force",
            "--file",
            env_file.name,
            "-p",
            env_prefix,
        ]
        return subprocess_args

    def _get_run_script_args(self, environment_path, script_full_path) -> List[str]:
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

    def _get_remove_env_args(self, path) -> List[str]:
        subprocess_args = [
            self.get_install_environment_executable(),
            "env",
            "remove",
            "-y",
            "-q",
            "-p",
            os.path.normpath(path),
        ]
        return subprocess_args
