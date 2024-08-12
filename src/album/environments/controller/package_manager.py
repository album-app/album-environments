"""Implementation of the PackageManager class."""
import json
import os
import platform
import tempfile
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Union

import yaml
from album.runner.album_logging import get_active_logger

from album.environments.api.controller.package_manager import IPackageManager
from album.environments.api.model.environment import IEnvironment
from album.environments.model.environment_default_values import EnvironmentDefaultValues
from album.environments.utils import subcommand
from album.environments.utils.file_operations import force_remove
from album.environments.utils.subcommand import SubProcessError


class PackageManager(IPackageManager):

    default_python_version = (
        EnvironmentDefaultValues.default_solution_python_version.value
    )

    def __init__(
        self, install_executable: str, package_manager_name: str, base_env_path: Path
    ):
        self._install_env_executable = install_executable
        self._package_manager_name = package_manager_name
        self._base_env_path = base_env_path

    def get_install_environment_executable(self) -> str:
        return self._install_env_executable

    def get_package_manager_name(self) -> str:
        return self._package_manager_name

    def get_environment_list(self) -> List[Path]:
        if Path(self._base_env_path).exists():
            return sorted(self._get_immediate_subdirectories(self._base_env_path))
        else:
            return []

    @staticmethod
    def _get_immediate_subdirectories(a_dir: Path) -> List[Path]:
        return [
            a_dir.joinpath(name).resolve()
            for name in os.listdir(str(a_dir))
            if os.path.isdir(os.path.join(str(a_dir), name))
        ]

    def environment_exists(self, environment_path: Union[Path, str, None]) -> bool:
        if environment_path is None:
            get_active_logger().warning("No environment path given!")
            return False

        environment_list = self.get_environment_list()
        environment_path = Path(environment_path)

        return (
            True
            if (
                environment_path
                and environment_path.resolve()
                in [env.resolve() for env in environment_list]
                and os.listdir(environment_path)
            )
            else False
        )

    def remove_environment(self, environment_path: Union[Path, str, None]) -> bool:
        if environment_path is None:
            get_active_logger().warning("No environment path given! Skipping...")
            return False

        if self.get_active_environment_path() == environment_path:
            get_active_logger().warning("Cannot remove active environment! Skipping...")
            return False

        if not self.environment_exists(environment_path):
            get_active_logger().warning("Environment does not exist! Skipping...")
            return False

        try:
            subprocess_args = self._get_remove_env_args(Path(environment_path))  # type: ignore
            subcommand.run(subprocess_args, log_output=False)
        except SubProcessError:
            get_active_logger().debug(
                "Can't delete environment via command line call, deleting the folder next..."
            )
        force_remove(environment_path)
        return True

    def get_info(self) -> Dict[str, str]:
        subprocess_args = [self.get_install_environment_executable(), "info", "--json"]
        output = subcommand.check_output(subprocess_args)
        return json.loads(output)

    def list_environment(self, environment_path: Path) -> Dict[str, str]:
        subprocess_args = [
            self.get_install_environment_executable(),
            "list",
            "--json",
            "--prefix",
            str(environment_path),
        ]
        output = subcommand.check_output(subprocess_args)
        return json.loads(output)

    def create_environment(
        self,
        environment_path: str,
        python_version: Optional[str] = default_python_version,
        force: bool = False,
    ) -> None:
        env_exists = self.environment_exists(environment_path)
        if force and env_exists:
            self.remove_environment(environment_path)
        else:
            if env_exists:
                raise OSError(
                    "Environment with name %s already exists!" % environment_path
                )

            env_content = {
                "channels": ["conda-forge"],
                "dependencies": ["python=%s" % python_version],
            }
            self._install(environment_path, env_content)

    def create_environment_from_file(
        self, yaml_path: Path, environment_path: str
    ) -> None:
        if self.environment_exists(environment_path):
            self.remove_environment(environment_path)

        if not (str(yaml_path).endswith(".yml") or str(yaml_path).endswith(".yaml")):
            raise NameError("File needs to be a yml or yaml file!")

        yaml_path = Path(yaml_path)

        if not (yaml_path.is_file() and yaml_path.stat().st_size > 0):
            raise ValueError("File not a valid yml file!")

        with open(yaml_path) as f:
            content = yaml.safe_load(f)

        self._install(environment_path, content)

    def _install(
        self,
        environment_path: str,
        environment_content: Union[
            Mapping,
            None,
        ] = None,
    ) -> None:
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
                get_active_logger().debug("Cleanup failed environment creation...")
                self.remove_environment(environment_path)
            raise RuntimeError("Command failed due to reasons above!") from e
        finally:
            os.remove(env_file.name)

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
        if environment.path() is None:
            raise OSError(
                "Could not find environment %s. Is the solution installed?"
                % environment.name()
            )

        get_active_logger().debug("run_in_environment: %s..." % str(environment.path()))

        subprocess_args = self._get_run_script_args(environment.path(), script)  # type: ignore
        if argv and len(argv) > 1:
            subprocess_args.extend(argv[1:])
        subcommand.run(
            subprocess_args, pipe_output=pipe_output, env=environment_variables
        )

    def get_package_version(self, environment_path: Path, package_name: str) -> str:
        env_list = self.list_environment(environment_path)

        for package in env_list:
            if package["name"] == package_name:  # type: ignore
                return package["version"]  # type: ignore

        pypi_packages = self.get_installed_pypi_packages(environment_path)
        for pypi_package in pypi_packages:
            if pypi_package["name"] == package_name:  # type: ignore
                return pypi_package["version"]  # type: ignore
        return ""

    def is_installed(
        self,
        environment_path: Path,
        package_name: str,
        package_version: Union[str, None] = None,
        min_package_version: Union[str, None] = None,
    ) -> bool:
        env_list = self.list_environment(environment_path)

        for package in env_list:
            if package["name"] == package_name:  # type: ignore
                if package_version:
                    if package["version"] == package_version:  # type: ignore
                        get_active_logger().debug(
                            "Package %s:%s is installed..."
                            % (package_name, package_version)
                        )
                        return True
                    else:
                        get_active_logger().debug(
                            "Package %s:%s is not installed."
                            % (package_name, package["version"])  # type: ignore
                        )
                        return False
                if min_package_version:
                    if package["version"] == min_package_version:  # type: ignore
                        get_active_logger().debug(
                            "Package %s:%s is installed..."
                            % (package_name, min_package_version)
                        )
                        return True
                    if package["version"] < min_package_version:  # type: ignore
                        get_active_logger().debug(
                            "Package %s:%s is installed. Requirements not set! Reinstalling..."
                            % (package_name, package["version"])  # type: ignore
                        )
                        return False
                    if package["version"] > min_package_version:  # type: ignore
                        get_active_logger().debug(
                            "Package %s:%s is installed. Version should be compatible..."
                            % (package_name, package["version"])  # type: ignore
                        )
                        return True
                else:
                    get_active_logger().debug(
                        "Package %s:%s is installed..."
                        % (package_name, package["version"])  # type: ignore
                    )
                    return True

        return False

    def create_or_update_env(
        self,
        environment: IEnvironment,
        default_python_version: Optional[str] = default_python_version,
    ) -> None:
        if environment.path() is None:
            raise OSError(
                "Could not find environment %s. Is the solution installed?"
                % environment.name()
            )
        if self.environment_exists(environment.path()):  # type: ignore
            self.update(environment)
        else:
            self.create(environment, default_python_version)

    def create(
        self,
        environment: IEnvironment,
        default_python_version: Optional[str] = default_python_version,
    ) -> None:
        env_path = environment.path()
        yml_path = environment.yaml_file()
        if env_path is None:
            raise OSError(
                "Could not install environment %s. Path not set!" % environment.name()
            )

        if yml_path is not None:
            self.create_environment_from_file(yml_path, str(env_path))
        else:
            get_active_logger().warning(
                "No yaml file specified. Creating Environment without dependencies!"
            )

            self.create_environment(str(env_path), default_python_version)

    def update(self, environment: IEnvironment) -> None:
        get_active_logger().debug(
            "Skip installing environment %s..." % environment.name()
        )
        pass  # ToDo: implement and change log message

    def install(
        self,
        environment: IEnvironment,
        default_python_version: Optional[str] = default_python_version,
    ) -> None:
        self.create_or_update_env(environment, default_python_version)

    def get_installed_pypi_packages(self, environment_path: Path) -> Dict[str, str]:
        if self.is_installed(environment_path, "pip"):
            subprocess_args = self._get_pypi_list_args(str(environment_path))
            try:
                # todo: check if correct. Seems to list more packages than installed
                output = subcommand.check_output(subprocess_args)
                return json.loads(output)
            except RuntimeError as e:
                get_active_logger().error(
                    "Error while listing installed packages in environment: %s", e
                )
                return {}
        return {}

    @staticmethod
    def _get_pip_exe(environment_path: str) -> str:
        p = (
            platform.system()
        )  # Returns system/OS name: 'Linux', 'Darwin', 'Java', 'Windows'. Empty if the value cannot be determined.
        if p == "Windows":
            # NOTE: WHEN USING 'CONDA RUN' THE CORRECT ENVIRONMENT GETS TEMPORARY ACTIVATED,
            # BUT THE PATH POINTS TO THE WRONG PYTHON (conda base folder python) BECAUSE THE CONDA BASE PATH
            # COMES FIRST IN ENVIRONMENT VARIABLE "%PATH%". THUS, FULL PATH IS NECESSARY TO CALL
            # THE CORRECT PYTHON OR PIP! ToDo: keep track of this!
            return os.path.normpath(
                Path(environment_path).joinpath("Scripts", "pip.exe")
            )
        elif p == "Darwin" or p == "Linux":
            return os.path.normpath(Path(environment_path).joinpath("bin", "pip"))
        else:
            get_active_logger().warning(
                "Unsupported platform: %s! Trying linux based pathing." % p
            )
            return os.path.normpath(Path(environment_path).joinpath("bin", "pip"))

    def base_install(
        self,
        package_name: str,
        version: Union[str, None] = None,
        channel: str = "conda-forge",
    ) -> None:
        subproc_args = self._get_base_install_package_args(
            package_name, version, channel
        )
        subcommand.run(subproc_args, pipe_output=True)

    def get_base_environment_path(self) -> Path:
        info_dict = self.get_info()
        k = self._get_base_env_key()

        return Path(info_dict[k])
