import os
import platform
import shutil
from pathlib import Path

from album.environments.api.controller.environment_handler import IEnvironmentHandler
from album.environments.controller.conda_lock_manager import CondaLockManager
from album.environments.controller.conda_manager import CondaManager
from album.environments.controller.environment_handler import EnvironmentHandler
from album.environments.controller.mamba_manager import MambaManager
from album.environments.controller.micromamba_manager import MicromambaManager
from album.runner.album_logging import get_active_logger


class PackageManagerDetector:
    def __init__(self, base_env_path, micromamba_path=None, conda_path=None, mamba_path=None, conda_lock_path=None):
        self._conda_executable = None
        self._mamba_executable = None
        self._micromamba_executable = None
        self._conda_lock_executable = None

        # explicitly defined package manager
        if micromamba_path is not None:
            self._micromamba_executable = micromamba_path
            get_active_logger().debug("Using micromamba executable: %s", self._micromamba_executable)
        elif conda_path is not None:
            self._conda_executable = conda_path

            # check if mamba is available and favor it over conda
            if mamba_path is not None:
                self._mamba_executable = mamba_path
                get_active_logger().debug("Using mamba executable: %s", self._mamba_executable)
            else:
                get_active_logger().debug("Using conda executable: %s", self._conda_executable)
        elif mamba_path is not None:
            self._mamba_executable = mamba_path
            get_active_logger().debug("Using mamba executable: %s", self._mamba_executable)
        else:  # search for a package manager with default values
            self.search_package_manager(micromamba_path)

        # check for conda-lock
        if conda_lock_path is None:
            self._conda_lock_executable = self.search_lock_manager()

        self._package_manager = self.create_package_manager(base_env_path)
        self._conda_lock_manager = CondaLockManager(self._conda_lock_executable, self._package_manager)

    @staticmethod
    def search_lock_manager():
        conda_lock_executable = shutil.which("conda-lock")
        if conda_lock_executable:
            get_active_logger().debug("Using conda-lock executable: %s", conda_lock_executable)
        else:
            get_active_logger().debug("No conda-lock executable found! Cannot lock environments during deployment!")
        return conda_lock_executable

    def search_package_manager(self, micromamba_path):
        if micromamba_path and Path(micromamba_path).is_file():  # look in default micromamba location
            # points to the executable, e.g. /path/bin/micromamba
            self._micromamba_executable = micromamba_path
            get_active_logger().debug("Using micromamba executable: %s", self._micromamba_executable)
        else:
            # search for micromamba
            self._micromamba_executable = shutil.which("micromamba")
            if self._micromamba_executable is not None:
                get_active_logger().debug("Using micromamba executable: %s", self._micromamba_executable)
            else:
                # search for conda
                self._conda_executable = shutil.which("conda")
                if self._conda_executable is not None:
                    # additionally search for mamba
                    self._mamba_executable = shutil.which("mamba")
                    if self._mamba_executable is not None:
                        get_active_logger().debug("Using mamba executable: %s", self._mamba_executable)
                    else:
                        get_active_logger().debug("Using conda executable: %s", self._conda_executable)
                else:
                    raise RuntimeError("No package manager found!")

    def create_package_manager(self, base_env_path):
        if self._micromamba_executable:
            return MicromambaManager(self._micromamba_executable, base_env_path=base_env_path)
        elif self._mamba_executable:
            return MambaManager(self._mamba_executable, base_env_path=base_env_path)
        else:
            return CondaManager(self._conda_executable, base_env_path=base_env_path)

    def get_conda_lock_manager(self):
        return self._conda_lock_manager

    def get_package_manager(self):
        return self._package_manager


def init_environment_handler(env_base_path, micromamba_path=None, conda_path=None, mamba_path=None, conda_lock_path=None) -> IEnvironmentHandler:
    package_manager_detector = PackageManagerDetector(env_base_path, micromamba_path, mamba_path, conda_path, conda_lock_path)
    package_manager = package_manager_detector.get_package_manager()
    conda_lock_manager = package_manager_detector.get_conda_lock_manager()
    return EnvironmentHandler(package_manager, conda_lock_manager)
