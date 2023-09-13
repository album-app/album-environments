from abc import abstractmethod

from album.environments.api.model.environment import IEnvironment
from album.runner import album_logging

module_logger = album_logging.get_active_logger


class IPackageManager:
    """Parent class for all package managers, like Conda, Mamba, Micromamba, etc."""

    @abstractmethod
    def get_install_environment_executable(self):
        raise NotImplementedError

    @abstractmethod
    def get_package_manager_name(self):
        raise NotImplementedError

    @abstractmethod
    def get_active_environment_name(self):
        """Returns the environment from the active album. Implemented in Child classes"""
        raise NotImplementedError

    @abstractmethod
    def get_active_environment_path(self):
        """Returns the environment for the active album. Implemented in Child classes"""
        raise NotImplementedError

    @abstractmethod
    def _get_env_create_args(self, env_file, env_prefix):
        """Returns the arguments for the environment creation command. Implemented in Child classes"""
        raise NotImplementedError

    @abstractmethod
    def _get_run_script_args(self, environment_path, script_full_path):
        """Returns the arguments for a conda run in solution env call. Implemented in Child classes"""
        raise NotImplementedError

    @abstractmethod
    def _get_remove_env_args(self, path):
        """Returns the arguments for the environment removal command. Implemented in Child classes"""
        raise NotImplementedError

    @abstractmethod
    def get_environment_list(self):
        """Returns the available album conda environments."""
        raise NotImplementedError

    @abstractmethod
    def environment_exists(self, environment_path):
        """Checks whether an environment already exists or not.

        Args:
            environment_path:
                The path of an environment.

        Returns:
            True when environment exists else false.
        """
        raise NotImplementedError

    @abstractmethod
    def remove_environment(self, environment_path) -> bool:
        """Removes an environment given its path. Does nothing when environment does not exist.

        Args:
            environment_path:
                The path of the environment to remove

        Returns:
            True, when removal succeeded, else False

        """
        raise NotImplementedError

    @abstractmethod
    def get_info(self):
        """Get the info of the conda installation on the corresponding system.

        Returns:
            dictionary corresponding to conda info.
        """
        raise NotImplementedError

    @abstractmethod
    def list_environment(self, environment_path):
        """Lists all available packages in the given environment.

        Args:
            environment_path:
                The prefix of the environment to list.

        Returns:
            dictionary containing the available packages in the given conda environment.
        """
        raise NotImplementedError

    @abstractmethod
    def create_environment(self, environment_path, python_version, force=False):
        """Creates a conda environment with python (latest version) installed.

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
    def create_environment_from_file(self, yaml_path, environment_path):
        """Creates an environment given a path to a yaml file and its path.

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
    def is_installed(self, environment_path: str, package_name, min_package_version=None):
        """Checks if package is installed in a certain version."""
        raise NotImplementedError

    @abstractmethod
    def create_or_update_env(self, environment: IEnvironment, default_python_version: str):
        """Creates or updates the environment"""
        raise NotImplementedError

    @abstractmethod
    def create(self, environment: IEnvironment, default_python_version: str):
        """Creates environment a solution runs in."""
        raise NotImplementedError

    @abstractmethod
    def update(self, environment: IEnvironment):
        """Updates the environment"""
        raise NotImplementedError

    @abstractmethod
    def install(self, environment: IEnvironment, default_python_version: str):
        """Creates or updates an an environment."""
        raise NotImplementedError
