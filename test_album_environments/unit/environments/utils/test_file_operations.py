import os
import pathlib
import stat
import tempfile
import unittest.mock
from pathlib import Path

from album.environments.utils.file_operations import (
    get_dict_from_yml,
    write_dict_to_yml,
    create_path_recursively,
    force_remove,
    copy,
    copy_folder
)
from test_album_environments.test_common import TestCommon


class TestFileOperations(TestCommon):
    def setUp(self):
        super().setUp()
        self.set_dummy_solution_path()

    def tearDown(self) -> None:
        super().tearDown()

    def set_dummy_solution_path(self):
        current_path = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
        self.dummysolution = str(
            current_path.joinpath(
                "..", "..", "..", "..", "resources", "solution0_dummy.py"
            )
        )

    def test_get_dict_from_yml(self):

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_folder = Path(tmp_dir)

            tmp_yml_file = tmp_folder.joinpath("test_yaml")
            with open(tmp_yml_file, "w+") as f:
                f.write("test: [1, 2, 3]")
    
            d = get_dict_from_yml(tmp_yml_file)
            self.assertEqual(d, {"test": [1, 2, 3]})

    def test_get_dict_from_yml_string_only(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_folder = Path(tmp_dir)

            tmp_yml_file = tmp_folder.joinpath("test_yaml")
            with open(tmp_yml_file, "w+") as f:
                f.write("iAmOnlyAString")
    
            with self.assertRaises(TypeError):
                get_dict_from_yml(tmp_yml_file)

    def test_get_dict_from_yml_empty(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_folder = Path(tmp_dir)

            tmp_yml_file = tmp_folder.joinpath("test_yaml")
            tmp_yml_file.touch()
    
            with self.assertRaises(TypeError):
                get_dict_from_yml(tmp_yml_file)

    def test_write_dict_to_yml(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_folder = Path(tmp_dir)
            tmp_yml_file = tmp_folder.joinpath("test_yaml")
            tmp_yml_file.touch()
            self.assertEqual(tmp_yml_file.stat().st_size, 0)
            d = {"test": [1, 2, 3]}
            write_dict_to_yml(tmp_yml_file, d)
            self.assertTrue(tmp_yml_file.stat().st_size > 0)

    def test_create_path_recursively(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_folder = Path(tmp_dir).joinpath("test_folder", "new_folder")

            self.assertFalse(tmp_folder.is_dir())
    
            create_path_recursively(tmp_folder)
    
            self.assertTrue(tmp_folder.is_dir())

    def test_copy_folder(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
    
            # source
            source_copy = tmp_dir.joinpath("test_to_copy_folder")
            create_path_recursively(source_copy)
    
            source_copy_file_a = source_copy.joinpath("aFile.txt")
            source_copy_file_a.touch()
    
            source_copy_folder_inside = source_copy.joinpath("a_new_folder")
            create_path_recursively(source_copy_folder_inside)
    
            source_copy_file_b = source_copy_folder_inside.joinpath("bFile.txt")
            source_copy_file_b.touch()
    
            # target
            target_copy = tmp_dir.joinpath("test_copy_target_folder")
    
            # copy without root
            copy_folder(source_copy, target_copy, copy_root_folder=False)
    
            self.assertTrue(target_copy.joinpath("a_new_folder", "bFile.txt").exists())
            self.assertTrue(target_copy.joinpath("aFile.txt").exists())
    
            # copy with root
            target_copy = tmp_dir.joinpath("test_copy_target_folder_with_root")
    
            copy_folder(source_copy, target_copy, copy_root_folder=True)
    
            self.assertTrue(
                target_copy.joinpath(source_copy.name, "a_new_folder", "bFile.txt").exists()
            )
            self.assertTrue(target_copy.joinpath(source_copy.name, "aFile.txt").exists())

    def test_copy(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
        
            # source
            source_copy = tmp_dir.joinpath("test_to_copy_folder")
            create_path_recursively(source_copy)
            source_copy_file = source_copy.joinpath("aFile.txt")
            source_copy_file.touch()
    
            # target
            target_copy = tmp_dir.joinpath("test_unzip_target_folder")
            create_path_recursively(target_copy)
    
            # copy
            copy(source_copy_file, target_copy)  # to new target folder
            copy(
                source_copy_file, target_copy.joinpath("newname.txt")
            )  # to new target folder with new name
    
            # assert
            self.assertTrue(target_copy.joinpath("aFile.txt").exists())
            self.assertTrue(target_copy.joinpath("newname.txt").exists())

    def test_force_remove_no_folder(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
    
            p = tmp_dir.joinpath("not_exist")
    
            force_remove(p)

    def test_force_remove_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_folder = Path(tmp_dir)
            p = tmp_folder.joinpath("file_exist")
            p.touch()
    
            force_remove(p)

    def test_force_remove_file_permission_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)

            p = tmp_dir.joinpath("file_exist")

            # make file protected and check if fallback is executed
            p.touch()
            os.chmod(p, stat.S_IWRITE)  # make write protected

            force_remove(p)  # should not fail

    if __name__ == "__main__":
        unittest.main()
