import os
import tempfile
from pathlib import Path

import yaml

from album.environments.api.environment_api import IEnvironmentAPI
from album.environments.model.environment import Environment
from album.environments.utils.file_operations import write_dict_to_yml
from test_album_environments.test_common import TestCommon


class _TestIntegrationCondaLock(TestCommon):
    """Base class for testing conda lock file creation with various package manager."""

    def setUp(self):
        super().setUp()
        self.test_environment_path = self.test_base_envs.joinpath(self.test_environment_name)
        self.env_handler = self.init_env_handler()

    def init_env_handler(self) -> IEnvironmentAPI:
        raise NotImplementedError()

    def tearDown(self) -> None:
        if self.env_handler.get_package_manager().environment_exists(
            self.test_environment_path
        ):
            self.env_handler.get_package_manager().remove_environment(
                self.test_environment_path
            )
            self.assertFalse(
                self.env_handler.get_package_manager().environment_exists(
                    self.test_environment_path
                )
            )
        self.test_base_dir.cleanup()
        self.second_test_base_dir.cleanup()
        super().tearDown()

    def create_conda_lockfile(self):
        # prepare
        yml_dict = {
            "name": "t",
            "channels": ["conda-forge"],
            "dependencies": ["python"],
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_folder = Path(tmp_dir)
            yml_path = tmp_folder.joinpath("test.yml")
            write_dict_to_yml(yml_path, yml_dict)

            # call
            conda_lock_path = self.env_handler.get_conda_lock_manager().conda_lock_executable()
            self.assertIsNotNone(conda_lock_path)
            lock_file = (
                self.env_handler.get_conda_lock_manager().create_conda_lock_file(
                    yml_path, conda_lock_path
                )
            )

            # assert
            self.assertTrue(lock_file.is_file())
            self.assertEqual("solution.conda-lock.yml", lock_file.name)
            self.assertEqual(yml_path.parent, lock_file.parent)
            self.assertNotEqual(lock_file.stat().st_size, 0)

    def create_remove_environment(self):
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

    def create_environment_from_file_and_get_package_version(self):
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

    def run_script(self):
        self.env_handler.get_package_manager().create_environment(
            str(self.test_environment_path), "3.9.15"
        )
        self.assertTrue(
            self.env_handler.get_package_manager().environment_exists(self.test_environment_path)
        )

        os.environ["ENVIRONMENT_TEST_VARIABLE"] = "script_test_variable"
        # prepare
        script = "import sys; print(\"script_python_version=\" + str(sys.version)); print(sys.argv); import os; print(os.getenv('ENVIRONMENT_TEST_VARIABLE'))"
        script_path = Path(self.test_base_dir.name).joinpath("test_script.py")
        with open(script_path, "w") as f:
            f.write(script)

        e = Environment(
            yaml_file=None,
            environment_name=self.test_environment_name,
            environment_path=self.test_environment_path,
        )

        # call
        self.env_handler.get_package_manager().run_script(
            environment=e,
            script=str(script_path),
            environment_variables=os.environ,
            argv=["calling_python_file.py", "--test=1"],
            pipe_output=True,
        )

        # assert
        self.assertIn("script_python_version=3.9.15", self.captured_output.getvalue())  # correct python version in script
        self.assertIn("--test=1", self.captured_output.getvalue())  # argv passed correctly
        self.assertIn("script_test_variable", self.captured_output.getvalue())  # environment variable passed correctly
