import unittest

from album.environments.api.environment_api import IEnvironmentAPI
from album.environments.initialization import init_environment_handler
from test_album_environments.integration.environments.test_integration_conda_lock_base import (
    _TestIntegrationCondaLock,
)


class TestIntegrationCondaLockConda(_TestIntegrationCondaLock):
    def init_env_handler(self) -> IEnvironmentAPI:
        return init_environment_handler(self.test_base)

    def test_create_conda_lockfile(self):
        super().create_conda_lockfile()


if __name__ == "__main__":
    unittest.main()
