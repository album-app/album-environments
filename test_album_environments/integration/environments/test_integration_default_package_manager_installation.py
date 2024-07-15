import os
from pathlib import Path

from album.environments.api.environment_api import IEnvironmentAPI
from album.environments.initialization import init_environment_handler
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
        os.environ["ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"] = ""
        self.assertEqual("", os.environ.get("ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"))

        inst_path = Path(self.test_base_dir.name).joinpath("installation")
        inst_path.mkdir(exist_ok=True)

        eh = init_environment_handler(
            env_base_path=self.test_base_envs,
            installation_base_path=inst_path
        )

        print(eh.get_package_manager().get_install_environment_executable())
        self.assertNotEqual(manual_set_micromamba, eh.get_package_manager().get_install_environment_executable())
