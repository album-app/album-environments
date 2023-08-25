from abc import ABCMeta, abstractmethod

from album.environments.api.controller.package_manager import IPackageManager
from album.environments.api.model.environment import IEnvironment


class IEnvironmentHandler:
    """Manages everything around the environment a solution lives in."""

    __metaclass__ = ABCMeta

    @abstractmethod
    def create_environment_prefer_lock_file(self, environment, solution_lock_file):
        raise NotImplementedError

    @abstractmethod
    def install_environment(
        self, environment: IEnvironment, default_python_version
    ) -> IEnvironment:
        raise NotImplementedError

    @abstractmethod
    def remove_environment(self, environment: IEnvironment):
        """Removes an environment."""
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
        """Runs the solution in the target environment

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
        raise NotImplementedError

    @abstractmethod
    def get_conda_lock_manager(self):
        raise NotImplementedError
