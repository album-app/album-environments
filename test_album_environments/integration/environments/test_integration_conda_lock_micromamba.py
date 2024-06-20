import os
import unittest

from album.environments.api.environment_api import IEnvironmentAPI
from album.environments.initialization import init_environment_handler
from test_album_environments.integration.environments.test_integration_conda_lock_base import (
    _TestIntegrationCondaLock,
)


class TestIntegrationCondaLockMicromamba(_TestIntegrationCondaLock):
    def init_env_handler(self) -> IEnvironmentAPI:
        micromamba_path = os.getenv("ALBUM_MICROMAMBA_PATH", os.getenv("MAMBA_EXE", "micromamba"))
        conda_lock_path = os.getenv("ALBUM_CONDA_LOCK_PATH", "conda-lock")
        return init_environment_handler(
            self.test_base, micromamba_path=micromamba_path, conda_lock_path=conda_lock_path
        )

    def test_create_conda_lockfile(self):
        super().create_conda_lockfile()


if __name__ == "__main__":
    unittest.main()
