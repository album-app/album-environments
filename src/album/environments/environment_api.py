from pathlib import Path
from typing import List, Mapping, Optional, Union

from album.runner.album_logging import get_active_logger

from album.environments.api.controller.conda_lock_manager import ICondaLockManager
from album.environments.api.controller.package_manager import IPackageManager
from album.environments.api.environment_api import IEnvironmentAPI
from album.environments.api.model.environment import IEnvironment


class EnvironmentAPI(IEnvironmentAPI):
    def __init__(
        self,
        package_manager: IPackageManager,
        conda_lock_manager: ICondaLockManager,
    ):
        # get installed package manager
        self._package_manager = package_manager
        self._conda_lock_manager = conda_lock_manager

    def install_environment(
        self, environment: IEnvironment, default_python_version: Optional[str]
    ) -> None:
        self._package_manager.install(environment, default_python_version)

    def remove_environment(self, environment: IEnvironment) -> bool:
        res = self._package_manager.remove_environment(environment.path())
        return res

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
        if environment:
            self._package_manager.run_script(
                environment,
                script,
                environment_variables=environment_variables,
                argv=argv,
                pipe_output=pipe_output,
            )
        else:
            raise OSError("Environment not set! Cannot run scripts!")

    def get_package_manager(self) -> IPackageManager:
        return self._package_manager

    def get_conda_lock_manager(self) -> ICondaLockManager:
        return self._conda_lock_manager

    def create_environment_prefer_lock_file(
        self, environment: IEnvironment, solution_lock_file: str
    ) -> None:
        _solution_lock_file = Path(solution_lock_file)
        if (
            _solution_lock_file.is_file()
            and self._conda_lock_manager.conda_lock_executable() is not None
        ):
            get_active_logger().debug("Creating solution environment from lock file.")
            self._conda_lock_manager.create_environment_from_lockfile(
                _solution_lock_file, environment.path()  # type: ignore
            )
        else:
            self._package_manager.install(environment)

    def get_package_version(
        self, environment: IEnvironment, package: str, version: str
    ) -> str:
        environment_path = environment.path()

        if environment_path is None:
            raise ValueError("Environment path is not set!")

        if self._package_manager.environment_exists(environment_path):
            # check for album as a dependency and warn if present
            album_installed_version = self._package_manager.get_package_version(
                Path(environment_path), package
            )
            return album_installed_version
        return ""
