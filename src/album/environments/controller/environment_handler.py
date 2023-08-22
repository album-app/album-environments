import subprocess
import sys
from io import StringIO
from pathlib import Path

import validators

from album.environments.api.controller.environment_handler import IEnvironmentHandler
from album.environments.api.model.environment import IEnvironment
from album.environments.controller.conda_lock_manager import CondaLockManager
from album.environments.controller.package_manager import PackageManager
from album.environments.utils.file_operations import (
    copy,
    get_dict_from_yml,
    write_dict_to_yml,
)
from album.environments.utils.url_operations import download_resource
from album.runner.album_logging import get_active_logger


class EnvironmentHandler(IEnvironmentHandler):
    def __init__(self, package_manager, conda_lock_manager: CondaLockManager):
        # get installed package manager
        self._package_manager = package_manager
        self._conda_lock_manager = conda_lock_manager

    def install_environment(self, environment, default_python_version) -> IEnvironment:
        return self._package_manager.install(environment, default_python_version)

    def remove_environment(self, environment: IEnvironment) -> bool:
        """Removes an environment."""
        res = self._package_manager.remove_environment(environment.path())
        return res

    def run_script(
        self,
        environment: IEnvironment,
        script,
        environment_variables=None,
        argv=None,
        pipe_output=True,
    ):
        if environment:
            self._package_manager.run_script(
                environment,
                script,
                environment_variables=environment_variables,
                argv=argv,
                pipe_output=pipe_output,
            )
        else:
            raise EnvironmentError("Environment not set! Cannot run scripts!")

    def get_package_manager(self) -> PackageManager:
        return self._package_manager

    def get_conda_lock_manager(self) -> CondaLockManager:
        return self._conda_lock_manager

    @staticmethod
    def _prepare_env_file(dependencies_dict, cache_path, env_name):
        """Checks how to set up an environment. Returns a path to a valid yaml file. Environment name in that file
        will be overwritten!

        Args:
            dependencies_dict:
                Dictionary holding the "environment_file" key. Environment file can be:
                    - url
                    - path
                    - stream object

        Returns:
            Path to a valid yaml file where environment name has been replaced!

        """
        if dependencies_dict:
            if "environment_file" in dependencies_dict:
                env_file = dependencies_dict["environment_file"]

                yaml_path = cache_path.joinpath("%s%s" % (env_name, ".yml"))
                Path(yaml_path.parent).mkdir(parents=True, exist_ok=True)

                if isinstance(env_file, str):
                    # case valid url
                    if validators.url(env_file):
                        yaml_path = download_resource(env_file, yaml_path)
                    # case file content
                    elif "dependencies:" in env_file and "\n" in env_file:
                        with open(str(yaml_path), "w+") as f:
                            f.writelines(env_file)
                        yaml_path = yaml_path
                    # case Path
                    elif Path(env_file).is_file() and Path(env_file).stat().st_size > 0:
                        yaml_path = copy(env_file, yaml_path)
                    else:
                        raise TypeError(
                            "environment_file must either contain the content of the environment file, "
                            "contain the url to a valid file or point to a file on the disk!"
                        )
                # case String stream
                elif isinstance(env_file, StringIO):
                    with open(str(yaml_path), "w+") as f:
                        env_file.seek(0)  # make sure we start from the beginning
                        f.writelines(env_file.readlines())
                    yaml_path = yaml_path
                else:
                    raise RuntimeError(
                        "Environment file specified, but format is unknown!"
                        " Don't know where to run solution!"
                    )

                yaml_dict = get_dict_from_yml(yaml_path)
                yaml_dict["name"] = env_name
                write_dict_to_yml(yaml_path, yaml_dict)

                return yaml_path
            return None
        return None

    @staticmethod
    def check_for_executable(default_path):
        try:
            subprocess.run([default_path], capture_output=True)
            return True
        except FileNotFoundError:
            return False

    @staticmethod
    def build_conda_executable(conda_path):
        operation_system = sys.platform
        if operation_system == "linux" or operation_system == "darwin":
            return str(Path(conda_path).joinpath("bin", "conda"))
        else:
            return str(Path(conda_path).joinpath("Scripts", "conda.exe"))

    def create_environment_prefer_lock_file(self, environment, solution_lock_file):
        solution_lock_file = Path(solution_lock_file)
        if solution_lock_file.is_file() and self._conda_lock_manager._conda_lock_executable is not None:
            get_active_logger().debug("Creating solution environment from lock file.")
            self._conda_lock_manager.create_environment_from_lockfile(solution_lock_file, environment.path())
        else:
            self._package_manager.install(environment)
