import shutil
import tempfile
from pathlib import Path

from album.environments.api.controller.environment_handler import IEnvironmentHandler
from album.environments.utils.file_operations import write_dict_to_yml
from test_album_environments.test_common import TestCommon


class _TestIntegrationCondaLock(TestCommon):

    def setUp(self):
        super().setUp()
        self.tmp_dir_obj = tempfile.TemporaryDirectory()
        self.test_base = Path(self.tmp_dir_obj.name)
        self.test_environment_path = self.test_base.joinpath(self.test_environment_name)
        self.tmp_dir = Path(tempfile.TemporaryDirectory().name)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.env_handler = self.init_env_handler()

    def init_env_handler(self) -> IEnvironmentHandler:
        raise NotImplementedError()

    def tearDown(self) -> None:
        if self.env_handler.get_package_manager().environment_exists(self.test_environment_path):
            self.env_handler.get_package_manager().remove_environment(self.test_environment_path)
            self.assertFalse(self.env_handler.get_package_manager().environment_exists(self.test_environment_path))
        self.tmp_dir_obj.cleanup()
        super().tearDown()

    def create_conda_lockfile(self):
        # prepare
        yml_dict = {
            "name": "t",
            "channels": ["conda-forge"],
            "dependencies": ["python"]
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_folder = Path(tmp_dir)
            yml_path = tmp_folder.joinpath("test.yml")
            write_dict_to_yml(
                yml_path, yml_dict
            )

            # call
            conda_lock_path = shutil.which("conda-lock")
            self.assertIsNotNone(conda_lock_path)
            conda_lock_path = Path(conda_lock_path)
            lock_file = self.env_handler.get_conda_lock_manager().create_conda_lock_file(yml_path, conda_lock_path)

            # assert
            self.assertTrue(lock_file.is_file())
            self.assertEqual("solution.conda-lock.yml", lock_file.name)
            self.assertEqual(yml_path.parent, lock_file.parent)
            self.assertNotEqual(lock_file.stat().st_size, 0)
