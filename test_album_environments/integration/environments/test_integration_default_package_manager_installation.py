import os
from pathlib import Path

from album.environments.api.environment_api import IEnvironmentAPI
from album.environments.initialization import PackageManagerHandler
from test_album_environments.integration.environments.test_integration_conda_lock_base import (
    _TestIntegrationCondaLock,
)


class TestIntegrationCondaLockMicromamba(_TestIntegrationCondaLock):
    test_environment_name = "micromamba_test_environment"

    def setUp(self):
        super().setUp()

    def tearDown(self) -> None:
        # do not call super here
        pass

    def init_env_handler(self) -> IEnvironmentAPI:
        pass

    def test_init_env_handler_no_explicit_exe(self):
        manual_set_micromamba = os.environ.get("ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH")
        self.assertIsNotNone(manual_set_micromamba)

        # do not set any package manager, let micromamba from initialization be used, so delete the env var
        del os.environ["ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"]
        self.assertIsNone(os.environ.get("ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"))

        inst_path = Path(self.test_base_dir.name).joinpath("installation")
        inst_path.mkdir(exist_ok=True)

        package_manager_handler = PackageManagerHandler(
            base_env_path=self.test_base_envs,
            installation_path=inst_path,
            micromamba_path=None,
            mamba_path=None,
            conda_path=None,
            conda_lock_path=None,
        )
        package_manager = package_manager_handler.get_package_manager()
        self.assertNotEqual(manual_set_micromamba, package_manager._install_env_executable)
