import shutil
import tempfile
import unittest
from pathlib import Path

from album.environments.utils.conda_lock import create_conda_lock_file
from album.environments.utils.file_operations import write_dict_to_yml
from test_album_environments.test_common import TestCommon


class TestCondaLock(TestCommon):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_create_conda_lockfile(self):
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
            lock_file = create_conda_lock_file(yml_path, conda_lock_path)

            # assert
            self.assertTrue(lock_file.is_file())
            self.assertEqual("solution.conda-lock.yml", lock_file.name)
            self.assertEqual(yml_path.parent, lock_file.parent)
            self.assertNotEqual(lock_file.stat().st_size, 0)
