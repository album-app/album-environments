"""API class that exposes functionality to the album core."""
from abc import ABCMeta, abstractmethod
from typing import List, Mapping, Union

from album.environments.api.controller.conda_lock_manager import ICondaLockManager
from album.environments.api.controller.package_manager import IPackageManager
from album.environments.api.model.environment import IEnvironment


class IEnvironmentAPI:
    """API for everything around the environment a solution lives in.

    Provides the API exposed to the album core.
    Needs a package manager to install and remove environments.
    The package manager could be a conda, mamba or micromamba manager.

    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def create_environment_prefer_lock_file(
        self, environment: IEnvironment, solution_lock_file: str
    ) -> None:
        """Create an environment with the given lock file."""
        raise NotImplementedError

    @abstractmethod
    def install_environment(
        self, environment: IEnvironment, default_python_version: str
    ) -> None:
        """Install an environment."""
        raise NotImplementedError

    @abstractmethod
    def remove_environment(self, environment: IEnvironment) -> bool:
        """Remove an environment."""
        raise NotImplementedError

    @abstractmethod
    def run_script(
        self,
        environment: IEnvironment,
        script: str,
        environment_variables: Union[
            Mapping,
            None,
        ] = None,
        argv: Union[List[str], None] = None,
        pipe_output: bool = True,
    ) -> None:
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
    def get_package_manager(self) -> IPackageManager:
        """Get the package manager."""
        raise NotImplementedError

    @abstractmethod
    def get_conda_lock_manager(self) -> ICondaLockManager:
        """Get the conda lock manager."""
        raise NotImplementedError

    @abstractmethod
    def get_package_version(
        self, environment: IEnvironment, package: str, version: str
    ) -> str:
        """Get the version of a package in the environment.

        If the environment does not exist or the package is not installed, str will be empty.

        """
