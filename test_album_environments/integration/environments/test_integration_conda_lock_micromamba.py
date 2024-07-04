import os
import tempfile

import yaml

from album.environments.api.environment_api import IEnvironmentAPI
from album.environments.initialization import init_environment_handler
from test_album_environments.integration.environments.test_integration_conda_lock_base import (
    _TestIntegrationCondaLock,
)


class TestIntegrationCondaLockMicromamba(_TestIntegrationCondaLock):
    test_environment_name = "micromamba_test_environment"

    def init_env_handler(self) -> IEnvironmentAPI:
        micromamba_path = os.getenv("ALBUM_MICROMAMBA_PATH", os.getenv("MAMBA_EXE", "micromamba"))
        conda_lock_path = os.getenv("ALBUM_CONDA_LOCK_PATH", "conda-lock")
        return init_environment_handler(
            self.test_base, micromamba_path=micromamba_path, conda_lock_path=conda_lock_path
        )

    def test_create_conda_lockfile(self):
        super().create_conda_lockfile()

    def test_create_remove_environment(self):
        self.env_handler.get_package_manager().create_environment(
            self.test_environment_path, "3.9.15"
        )
        self.assertTrue(
            self.env_handler.get_package_manager().environment_exists(self.test_environment_path)
        )
        self.env_handler.get_package_manager().remove_environment(self.test_environment_path)
        self.assertFalse(
            self.env_handler.get_package_manager().environment_exists(self.test_environment_path)
        )

    def test_create_environment_from_file_and_get_package_version(self):
        # yml file:
        env_content = {
            "channels": ["conda-forge"],
            "dependencies": [
                "python=%s" % "3.9.15",
                              "pip",
                {"pip": ["pyyaml==5.4.1"]}
            ],
        }
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".yml"
        ) as env_file:
            env_file.write(yaml.safe_dump(env_content))

        self.env_handler.get_package_manager().create_environment_from_file(
             env_file.name, self.test_environment_path,
        )
        self.assertTrue(
            self.env_handler.get_package_manager().environment_exists(self.test_environment_path)
        )
        self.assertEqual(
            "5.4.1",
            self.env_handler.get_package_manager().get_package_version(
                self.test_environment_path, "PyYAML"
            )
        )
