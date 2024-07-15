import tempfile
from pathlib import Path

import yaml

from album.environments.api.environment_api import IEnvironmentAPI
from album.environments.initialization import init_environment_handler
from test_album_environments.integration.environments.test_integration_conda_lock_base import (
    _TestIntegrationCondaLock,
)


class TestIntegrationCondaLockMicromamba(_TestIntegrationCondaLock):
    test_environment_name = "micromamba_test_environment"

    def init_env_handler(self) -> IEnvironmentAPI:
        # uses micromamba from CICD path
        return init_environment_handler(
            env_base_path=self.test_base_envs, installation_base_path=self.test_base_dir.name
        )

    def test_create_conda_lockfile(self):
        super().create_conda_lockfile()

    def test_create_remove_environment(self):
        self.env_handler.get_package_manager().create_environment(
            str(self.test_environment_path), "3.9.15"
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
            Path(env_file.name), str(self.test_environment_path),
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
