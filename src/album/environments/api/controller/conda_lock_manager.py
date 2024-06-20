"""Module for the ICondaLockManager interface."""
from abc import ABCMeta, abstractmethod
from pathlib import Path


class ICondaLockManager:
    """Class for creating conda environment from conda lock files.

    Since a separate executable is used, this functionality is separated from the CondaManager class.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def create_conda_lock_file(
        self, solution_yml: Path, conda_lock_executable: Path
    ) -> Path:
        """Create a conda lock file from a solution yml file."""
        raise NotImplementedError

    @abstractmethod
    def create_environment_from_lockfile(
        self, conda_lock_file: Path, environment_path: Path
    ) -> None:
        """Create a conda environment from a conda lock file.

        If the environment already exists, it will be removed first.
        """
        raise NotImplementedError

    @abstractmethod
    def conda_lock_executable(self) -> str:
        """Get the conda lock executable."""
        raise NotImplementedError
