import os
import unittest
from pathlib import Path

from album.environments.api.environment_api import IEnvironmentAPI
from album.environments.initialization import init_environment_handler
from test_album_environments.integration.environments.test_integration_conda_lock_base import (
    _TestIntegrationCondaLock,
)


class TestIntegrationCondaLockMamba(_TestIntegrationCondaLock):
    test_environment_name = "mamba_test_environment"

    def init_env_handler(self) -> IEnvironmentAPI:
        if os.environ["ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"]:
            del os.environ["ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"]

        if os.environ.get("ENVIRONMENT_DEBUGGING_CONDA_PATH"):
            del os.environ["ENVIRONMENT_DEBUGGING_CONDA_PATH"]

        # ensure no env vars are set
        self.assertIsNone(os.environ.get("ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"))
        self.assertIsNotNone(os.environ.get("ENVIRONMENT_DEBUGGING_MAMBA_PATH"))
        self.assertIsNone(os.environ.get("ENVIRONMENT_DEBUGGING_CONDA_PATH"))

        # uses mamba from CICD path
        return init_environment_handler(
            env_base_path=self.test_base_envs, installation_base_path=Path(self.test_base_dir.name)
        )

    def test_create_conda_lockfile(self):
        super().create_conda_lockfile()


if __name__ == "__main__":
    unittest.main()
