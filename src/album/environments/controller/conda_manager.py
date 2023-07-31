import json
import os
import sys
import tempfile
from pathlib import Path

import yaml

from album.environments.api.model.environment import IEnvironment
from album.environments.utils import subcommand
from album.environments.utils.file_operations import (
    force_remove,
)
from album.environments.utils.subcommand import SubProcessError
from album.runner import album_logging

module_logger = album_logging.get_active_logger


class CondaManager:
    """Class for handling conda environments.

    The conda class manages the environments a solution is supposed to run in. It provides all features necessary for
    environment creation, deletion, dependency installation, etc.

    Notes:
        An installed \"conda\" program must be available and callable via commandline or powershell.

    """

    default_python_version = "3.10"

    def __init__(self, conda_executable, base_env_path):
        self._conda_executable = conda_executable
        self._base_env_path = base_env_path

    def _get_install_environment_executable(self):
        return self._conda_executable

    def get_environment_list(self):
        """Returns the available album conda environments."""
        if Path(self._get_base_environment_target_path()).exists():
            return sorted(
                self._get_immediate_subdirectories(
                    self._get_base_environment_target_path()
                )
            )
        else:
            return []

    @staticmethod
    def _get_immediate_subdirectories(a_dir: Path):
        return [
            a_dir.joinpath(name).resolve()
            for name in os.listdir(str(a_dir))
            if os.path.isdir(os.path.join(str(a_dir), name))
        ]

    def _get_base_environment_target_path(self):
        """Gets the first of the paths the conda installation uses to manage its environments."""
        return self._base_env_path

    def environment_exists(self, env_path: Path):
        """Checks whether an environment already exists or not.

        Args:
            env_path:
                The path of an environment

        Returns:
            True when environment exists else false.
        """
        environment_list = self.get_environment_list()
        env_path = Path(env_path)

        return (
            True
            if (
                    env_path
                    and env_path.resolve() in environment_list
                    and os.listdir(env_path)
            )
            else False
        )

    def get_active_environment_name(self):
        """Returns the environment from the active album."""
        environment_info = self.get_info()
        return environment_info["active_prefix_name"]

    def get_active_environment_path(self):
        """Returns the environment form the active album."""
        environment_info = self.get_info()
        return environment_info["active_prefix"]

    def remove_environment(self, environment_path) -> bool:
        """Removes an environment given its name. Does nothing when environment does not exist.

        Args:
            environment_path:
                The name of the environment to remove

        Returns:
            True, when removal succeeded, else False

        """
        if self.get_active_environment_path() == environment_path:
            module_logger().warning("Cannot remove active environment! Skipping...")
            return False

        if not self.environment_exists(environment_path):
            module_logger().warning("Environment does not exist! Skipping...")
            return False

        try:
            subprocess_args = self._get_remove_env_args(environment_path)
            subcommand.run(subprocess_args, log_output=False)
        except SubProcessError:
            module_logger().debug(
                "Can't delete environment via command line call, deleting the folder next..."
            )
        # try to remove file content if any but don't fail:
        force_remove(environment_path)
        return True

    def get_info(self):
        """Get the info of the conda installation on the corresponding system.

        Returns:
            dictionary corresponding to conda info.
        """
        subprocess_args = [self._get_install_environment_executable(), "info", "--json"]
        output = subcommand.check_output(subprocess_args)
        return json.loads(output)

    def list_environment(self, environment_path):
        """Lists all available conda installation in the given environment.

        Args:
            environment_path:
                The prefix of the environment to list.

        Returns:
            dictionary containing the available packages in the given conda environment.
        """
        subprocess_args = [
            self._get_install_environment_executable(),
            "list",
            "--json",
            "--prefix",
            str(environment_path),
        ]
        output = subcommand.check_output(subprocess_args)
        return json.loads(output)

    def create_environment_from_file(self, yaml_path, environment_path: Path):
        """Creates a conda environment given a path to a yaml file and its name.

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
        if self.environment_exists(environment_path):
            self.remove_environment(environment_path)

        if not (str(yaml_path).endswith(".yml") or str(yaml_path).endswith(".yaml")):
            raise NameError("File needs to be a yml or yaml file!")

        yaml_path = Path(yaml_path)

        if not (yaml_path.is_file() and yaml_path.stat().st_size > 0):
            raise ValueError("File not a valid yml file!")

        with open(yaml_path, "r") as f:
            content = yaml.safe_load(f)

        self._install(environment_path, content)

    def create_environment(self, environment_path, python_version=default_python_version, force=False):
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
        env_exists = self.environment_exists(environment_path)
        if force and env_exists:
            self.remove_environment(environment_path)
        else:
            if env_exists:
                raise EnvironmentError(
                    "Environment with name %s already exists!" % environment_path
                )

        env_content = {
            "channels": ["defaults"],
            "dependencies": ["python=%s" % python_version],
        }

        self._install(environment_path, env_content)

    def _install(self, environment_path, environment_content):

        env_prefix = os.path.normpath(environment_path)
        force_remove(env_prefix)
        with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".yml"
        ) as env_file:

            env_file.write(yaml.safe_dump(environment_content))
        subprocess_args = self._get_env_create_args(env_file, env_prefix)
        try:
            subcommand.run(subprocess_args, log_output=True)
        except RuntimeError as e:
            # cleanup after failed installation
            if self.environment_exists(environment_path):
                module_logger().debug("Cleanup failed environment creation...")
                self.remove_environment(environment_path)
            raise RuntimeError("Command failed due to reasons above!") from e
        finally:
            os.remove(env_file.name)

    def _get_env_create_args(self, env_file, env_prefix):
        subprocess_args = [
            self._get_install_environment_executable(),
            "env",
            "create",
            "--force",
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
                self._conda_executable,
                "run",
                "--no-capture-output",
                "--prefix",
                os.path.normpath(environment_path),
                os.path.normpath(Path(environment_path).joinpath("python")),
                os.path.normpath(script_full_path),
            ]
        else:
            subprocess_args = [
                self._conda_executable,
                "run",
                "--no-capture-output",
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
            "env",
            "remove",
            "-y",
            "-q",
            "-p",
            os.path.normpath(path),
        ]
        return subprocess_args

    def is_installed(
            self, environment_path: Path, package_name, min_package_version=None
    ):
        """Checks if package is installed in a certain version."""
        conda_list = self.list_environment(environment_path)

        for package in conda_list:
            if package["name"] == package_name:
                if min_package_version:
                    if package["version"] == min_package_version:
                        module_logger().debug(
                            "Package %s:%s is installed..."
                            % (package_name, min_package_version)
                        )
                        return True
                    if package["version"] < min_package_version:
                        module_logger().debug(
                            "Package %s:%s is installed. Requirements not set! Reinstalling..."
                            % (package_name, package["version"])
                        )
                        return False
                    if package["version"] > min_package_version:
                        module_logger().debug(
                            "Package %s:%s is installed. Version should be compatible..."
                            % (package_name, package["version"])
                        )
                        return True
                else:
                    module_logger().debug(
                        "Package %s:%s is installed..."
                        % (package_name, package["version"])
                    )
                    return True

        return False

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
        if not environment.path():
            raise EnvironmentError(
                "Could not find environment %s. Is the solution installed?"
                % environment.name()
            )

        module_logger().debug("run_in_environment: %s..." % str(environment.path()))

        subprocess_args = self._get_run_script_args(environment.path(), script)
        if argv and len(argv) > 1:
            subprocess_args.extend(argv[1:])
        subcommand.run(
            subprocess_args, pipe_output=pipe_output, env=environment_variables
        )

    def create_or_update_env(
            self, environment: IEnvironment, default_python_version: str = default_python_version
    ):
        """Creates or updates the environment"""
        if self.environment_exists(environment.name()):
            self.update(environment)
        else:
            self.create(environment, default_python_version)

    def update(self, environment: IEnvironment):
        """Updates the environment"""
        module_logger().debug("Skip installing environment %s..." % environment.name())
        pass  # ToDo: implement and change log message

    def create(self, environment: IEnvironment, default_python_version: str = default_python_version):
        """Creates environment a solution runs in."""
        if environment.yaml_file():
            self.create_environment_from_file(
                environment.yaml_file(), environment.path()
            )
        else:
            module_logger().warning(
                "No yaml file specified. Creating Environment without dependencies!"
            )
            self.create_environment(environment.path(), default_python_version)

    def install(self, environment: IEnvironment, default_python_version):
        """Creates or updates an an environment and installs album in the target environment."""
        self.create_or_update_env(environment, default_python_version)
