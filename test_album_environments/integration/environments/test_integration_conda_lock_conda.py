import os
import unittest
from pathlib import Path

from album.environments.api.environment_api import IEnvironmentAPI
from album.environments.environment_api import EnvironmentAPI
from album.environments.initialization import init_environment_handler, PackageManagerHandler
from test_album_environments.integration.environments.test_integration_conda_lock_base import (
    _TestIntegrationCondaLock,
)


class TestIntegrationCondaLockConda(_TestIntegrationCondaLock):
    test_environment_name = "conda_test_environment"

    def init_env_handler(self) -> IEnvironmentAPI:
        if "ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH" in os.environ.keys():
            if os.environ["ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"]:
                del os.environ["ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"]

        if "ENVIRONMENT_DEBUGGING_MAMBA_PATH" in os.environ.keys():
            if os.environ.get("ENVIRONMENT_DEBUGGING_MAMBA_PATH"):
                del os.environ["ENVIRONMENT_DEBUGGING_MAMBA_PATH"]

        # ensure no env vars are set
        self.assertIsNone(os.environ.get("ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"))
        self.assertIsNone(os.environ.get("ENVIRONMENT_DEBUGGING_MAMBA_PATH"))
        self.assertIsNotNone(os.environ.get("ENVIRONMENT_DEBUGGING_CONDA_PATH"))

        # uses conda from CICD path
        package_manager_handler = PackageManagerHandler(
            base_env_path=str(self.test_base_envs),
            installation_path=str(Path(self.test_base_dir.name)),
            micromamba_path=None,
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


if __name__ == "__main__":
    unittest.main()
