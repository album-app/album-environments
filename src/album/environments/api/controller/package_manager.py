"""Interface for package managers, like Conda, Mamba, Micromamba, etc."""
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from album.environments.api.model.environment import IEnvironment


class IPackageManager:
    """Parent class for all package managers, like Conda, Mamba, Micromamba, etc."""

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_install_environment_executable(self):
        """Return the executable for the environment creation."""
        raise NotImplementedError

    @abstractmethod
    def get_package_manager_name(self):
        """Return the name of the package manager."""
        raise NotImplementedError

    @abstractmethod
    def get_active_environment_name(self) -> str:
        """Return the environment from the active album."""
        raise NotImplementedError

    @abstractmethod
    def get_active_environment_path(self) -> str:
        """Return the environment for the active album."""
        raise NotImplementedError

    @abstractmethod
    def _get_env_create_args(self, env_file, env_prefix) -> List[str]:
        """Return the arguments for the environment creation command."""
        raise NotImplementedError

    @abstractmethod
    def _get_run_script_args(self, environment_path, script_full_path) -> List[str]:
        """Return the arguments for a conda run in solution env call."""
        raise NotImplementedError

    @abstractmethod
    def _get_remove_env_args(self, path) -> List[str]:
        """Return the arguments for the environment removal command."""
        raise NotImplementedError

    @abstractmethod
    def get_environment_list(self) -> List[Path]:
        """Return the available album conda environments."""
        raise NotImplementedError

    @abstractmethod
    def environment_exists(self, environment_path: str) -> bool:
        """Check whether an environment already exists or not.

        Args:
            environment_path:
                The path of an environment.

        Returns:
            True when environment exists else false.
        """
        raise NotImplementedError

    @abstractmethod
    def remove_environment(self, environment_path: str) -> bool:
        """Remove an environment given its path.

        Does nothing when environment does not exist.

        Args:
            environment_path:
                The path of the environment to remove

        Returns:
            True, when removal succeeded, else False

        """
        raise NotImplementedError

    @abstractmethod
    def get_info(self) -> Dict[str, str]:
        """Get the info of the conda installation on the corresponding system.

        Returns:
            dictionary corresponding to conda info.
        """
        raise NotImplementedError

    @abstractmethod
    def list_environment(self, environment_path: str) -> Dict[str, str]:
        """List all available packages in the given environment.

        Args:
            environment_path:
                The prefix of the environment to list.

        Returns:
            dictionary containing the available packages in the given conda environment.
        """
        raise NotImplementedError

    @abstractmethod
    def create_environment(
        self, environment_path: str, python_version: Optional[str], force: bool = False
    ):
        """Create a conda environment with python (latest version) installed.

        Args:
            environment_path:
                The desired environment path.
            python_version:
                The python version to be installed into the environment
            force:
                If True, force creates the environment by deleting the old one.

        Raises:
            RuntimeError:
                When the environment could not be created due to whatever reasons.

        """
        raise NotImplementedError

    @abstractmethod
    def create_environment_from_file(self, yaml_path: str, environment_path: str):
        """Create an environment given a path to a yaml file and its path.

        Args:
            yaml_path:
                The path to the file.
            environment_path:
                The path of the environment.

        Raises:
            NameError:
                When the file has the wrong format according to its extension.
            ValueError:
                When the file is unreadable or empty.
            RuntimeError:
                When the environment could not be created due to whatever reasons.

        """
        raise NotImplementedError

    @abstractmethod
    def run_script(
        self,
        environment: IEnvironment,
        script,
        environment_variables=None,
        argv=None,
        pipe_output=True,
    ):
        """Run the solution in the target environment.

        Args:
            script:
                Script calling the solution
            environment:
                The virtual environment used to run the script
            environment_variables:
                The environment variables to attach to the script process
            argv:
                The arguments to attach to the script process
            pipe_output:
                Indicates whether to pipe the output of the subprocess or just return it as is.
        """
        raise NotImplementedError

    @abstractmethod
    def is_installed(
        self, environment_path: str, package_name, min_package_version=None
    ) -> bool:
        """Check if package is installed in a certain version."""
        raise NotImplementedError

    @abstractmethod
    def create_or_update_env(
        self, environment: IEnvironment, default_python_version: Optional[str]
    ):
        """Create or update the environment."""
        raise NotImplementedError

    @abstractmethod
    def create(self, environment: IEnvironment, default_python_version: Optional[str]):
        """Create environment a solution runs in."""
        raise NotImplementedError

    @abstractmethod
    def update(self, environment: IEnvironment):
        """Update the environment."""
        raise NotImplementedError

    @abstractmethod
    def install(self, environment: IEnvironment, default_python_version: Optional[str]):
        """Create or updates an environment."""
        raise NotImplementedError
