import os
from pathlib import Path

from album.environments.api.environment_api import IEnvironmentAPI
from album.environments.environment_api import EnvironmentAPI
from album.environments.initialization import PackageManagerHandler
from test_album_environments.integration.environments.test_integration_conda_lock_base import (
    _TestIntegrationCondaLock,
)


class TestIntegrationCondaLockMicromamba(_TestIntegrationCondaLock):
    test_environment_name = "micromamba_test_environment"

    def init_env_handler(self) -> IEnvironmentAPI:
        if "ENVIRONMENT_DEBUGGING_CONDA_PATH" in os.environ.keys():
            if os.environ["ENVIRONMENT_DEBUGGING_CONDA_PATH"]:
                del os.environ["ENVIRONMENT_DEBUGGING_CONDA_PATH"]

        if "ENVIRONMENT_DEBUGGING_MAMBA_PATH" in os.environ.keys():
            if os.environ.get("ENVIRONMENT_DEBUGGING_MAMBA_PATH"):
                del os.environ["ENVIRONMENT_DEBUGGING_MAMBA_PATH"]

        # ensure no env vars are set
        self.assertIsNotNone(os.environ.get("ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"))
        self.assertIsNone(os.environ.get("ENVIRONMENT_DEBUGGING_MAMBA_PATH"))
        self.assertIsNone(os.environ.get("ENVIRONMENT_DEBUGGING_CONDA_PATH"))

        self.assertTrue(Path(os.environ.get("ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH")).exists())

        package_manager_handler = PackageManagerHandler(
            base_env_path=str(self.test_base_envs),
            installation_path=str(Path(self.test_base_dir.name)),
            micromamba_path=os.environ.get("ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"),
            mamba_path=None,
            conda_path=None,
            conda_lock_path=None,
        )

        # uses micromamba from CICD path
        return EnvironmentAPI(
            package_manager_handler.get_package_manager(),
            package_manager_handler.get_conda_lock_manager(),
        )

    def test_create_conda_lockfile(self):
        super().create_conda_lockfile()

    def test_create_remove_environment(self):
        super().create_remove_environment()

    def test_create_environment_from_file_and_get_package_version(self):
        super().create_environment_from_file_and_get_package_version()

    def test_run_script(self):
        super().run_script()
