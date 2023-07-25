
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from album.environments.controller.micromamba_manager import MicromambaManager
from album.environments.initialization import get_micromamba_path, init_micromamba_environment_handler
from album.environments.model.environment import Environment


class TestMicromambaManager(unittest.TestCase):
    test_environment_name = "unittest"

    def setUp(self):
        super().setUp()
        self.test_base_dir = tempfile.TemporaryDirectory()
        self.test_base = Path(self.test_base_dir.name)
        self.test_environment_path = self.test_base.joinpath(self.test_environment_name)
        self.tmp_dir_obj = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self.tmp_dir_obj.name)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.micromamba = init_micromamba_environment_handler(self.test_base).get_package_manager()

    def tearDown(self) -> None:
        if self.micromamba.environment_exists(self.test_environment_path):
            self.micromamba.remove_environment(self.test_environment_path)
            self.assertFalse(
                self.micromamba.environment_exists(self.test_environment_path)
            )
        self.test_base_dir.cleanup()
        self.tmp_dir_obj.cleanup()
        super().tearDown()

    def test_get_environment_list(self):
        base_dir = self.test_base
        expected = list()
        expected.append(base_dir.joinpath("envName1").resolve())
        expected.append(base_dir.joinpath("envName2").resolve())
        Path(expected[0]).joinpath("somefile").mkdir(parents=True)
        Path(expected[1]).joinpath("somefile").mkdir(parents=True)

        res = self.micromamba.get_environment_list()

        self.assertListEqual(expected, res)

    @patch("album.environments.controller.conda_manager.CondaManager.get_environment_list")
    def test_environment_exists(self, ged_mock):
        target = self.test_base.joinpath("envName1")
        target_not_existing = self.test_base.joinpath("notExitendEnvs")
        Path(target).joinpath("whatever").mkdir(parents=True)

        ged_mock.return_value = [target.resolve()]

        self.assertTrue(self.micromamba.environment_exists(target))
        self.assertFalse(self.micromamba.environment_exists(target_not_existing))

    @patch("album.environments.controller.conda_manager.CondaManager.get_info")
    def test_get_active_environment_name(self, ginfo_mock):
        ginfo_mock.return_value = {"environment": "envName1"}
        self.assertEqual("envName1", self.micromamba.get_active_environment_name())

    @patch("album.environments.controller.conda_manager.CondaManager.get_info")
    def test_get_active_environment_path(self, ginfo_mock):
        ginfo_mock.return_value = {"env location": "aEnvPath"}
        self.assertEqual("aEnvPath", str(self.micromamba.get_active_environment_path()))

    def test_get_info(self):
        r = self.micromamba.get_info()

        self.assertIn("environment", r)
        self.assertIn("env location", r)

    def test_list_environment(self):
        p = self.micromamba.get_active_environment_path()
        r = self.micromamba.list_environment(p)

        self.assertIsNotNone(r)

    def test_create_environment_from_file_valid_file(self):
        self.assertFalse(self.micromamba.environment_exists(self.test_environment_path))
        env_file = """channels:
- defaults
dependencies:
- python"""
        with open(self.tmp_dir.joinpath("env_file.yml"), "w") as f:
            f.writelines(env_file)
        self.micromamba.create_environment_from_file(
            self.tmp_dir.joinpath("env_file.yml"), self.test_environment_path
        )
        self.assertTrue(self.micromamba.environment_exists(self.test_environment_path))

    def test_create_environment_from_file_invalid(self):
        # wrong file ending
        with self.assertRaises(NameError):
            self.micromamba.create_environment_from_file(
                self.tmp_dir.joinpath("env.tiff"), self.test_environment_path
            )

    def test_create_environment_from_file_valid_but_empty(self):
        t = self.tmp_dir.joinpath("%s.yml" % self.test_environment_name)
        t.touch()
        # no content in file
        with self.assertRaises(ValueError):
            self.micromamba.create_environment_from_file(t, self.test_environment_path)

    def test_create_environment(self):
        self.assertFalse(self.micromamba.environment_exists(self.test_environment_path))

        skip = False  # The test checks if an environment error is raised when the same environment ist created two
        # times the skip variable is used two skip the second env creation call if the first one fails

        try:
            self.micromamba.create_environment(self.test_environment_path)
        except RuntimeError as err:
            print(err)
            skip = True

        if not skip:
            # create it again without force fails
            with self.assertRaises(EnvironmentError):
                self.micromamba.create_environment(self.test_environment_path)

            self.assertTrue(self.micromamba.environment_exists(self.test_environment_path))

            # check if python & pip installed
            self.assertTrue(
                self.micromamba.is_installed(
                    self.test_environment_path,
                    "python",
                )
            )
            self.assertTrue(
                self.micromamba.is_installed(
                    self.test_environment_path, "pip"
                )
            )
        else:
            unittest.skip("WARNING - CONDA ERROR!")

    @unittest.skip("Tested in tear_down() routine!")
    def test_remove_environment(self, active_env_mock):
        pass

    @patch("album.environments.utils.subcommand.run", return_value=True)
    def test_remove_environment_not_exist(self, run_mock):
        self.micromamba.create_environment(self.test_environment_path)
        run_mock.assert_called_once()

        # run_mock not called again
        self.micromamba.remove_environment("iDoNotExist")
        run_mock.assert_called_once()

    @patch("album.environments.controller.conda_manager.CondaManager.list_environment")
    def test_is_installed(self, list_environment_mock):
        list_environment_mock.return_value = json.loads(
            """[
                {
                    "base_url": "https://repo.anaconda.com/pkgs/main",
                    "build_number": 3,
                    "build_string": "hdb3f193_3",
                    "channel": "pkgs/main",
                    "dist_name": "python-3.9.5-hdb3f193_3",
                    "name": "python",
                    "platform": "linux-64",
                    "version": "3.9.5"
                }
            ]"""
        )
        environment = Environment(None, "aName", "aPath")
        self.assertTrue(self.micromamba.is_installed(environment.path(), "python"))
        self.assertTrue(self.micromamba.is_installed(environment.path(), "python", "3.9.5"))
        self.assertFalse(self.micromamba.is_installed(environment.path(), "python", "500.1"))
        self.assertTrue(self.micromamba.is_installed(environment.path(), "python", "2.7"))

    @patch(
        "album.environments.utils.subcommand.run",
        return_value="ranScript",
    )
    def test_run_script(self, run_mock):
        with tempfile.NamedTemporaryFile(mode="w") as tmp:
            tmp.write('print("%s")' % self.test_environment_name)
            environment = Environment(None, "aName", "aPath")
            self.micromamba.run_script(environment, tmp.name)
            run_mock.assert_called_once()

    @patch(
        "album.environments.utils.subcommand.run",
        return_value="ranScript",
    )
    def test_run_script_no_path(self, conda_run_mock):
        with tempfile.NamedTemporaryFile(mode="w") as tmp:
            tmp.write('print("%s")' % self.test_environment_name)
            environment = Environment(None, "aName")
            environment._path = None

            with self.assertRaises(EnvironmentError):
                self.micromamba.run_script(environment, tmp.name)
            conda_run_mock.assert_not_called()

    def test_create_or_update_env_no_env(self):
        update_mock = MagicMock()
        create_mock = MagicMock()
        self.micromamba.update = update_mock
        self.micromamba.create = create_mock
        environment = Environment(None, "aName", "aPath")

        self.micromamba.create_or_update_env(environment, None)

        create_mock.assert_called_once_with(environment, None)
        update_mock.assert_not_called()

    @patch("album.environments.controller.conda_manager.CondaManager.create")
    @patch("album.environments.controller.conda_manager.CondaManager.update")
    @patch("album.environments.controller.conda_manager.CondaManager.environment_exists")
    def test_create_or_update_env_env_present(
            self, ex_env_mock, update_mock, create_mock
    ):

        ex_env_mock.return_value = True
        environment = Environment(None, "aName", "aPath")

        self.micromamba.create_or_update_env(environment)

        update_mock.assert_called_once_with(environment)
        create_mock.assert_not_called()

    @unittest.skip("Needs to be implemented!")
    def test_update(self):
        # ToDo: implement
        pass

    @patch("album.environments.controller.conda_manager.CondaManager.create_environment")
    @patch(
        "album.environments.controller.conda_manager.CondaManager.create_environment_from_file"
    )
    def test_create_valid_yaml(
            self, create_environment_from_file_mock, create_environment_mock
    ):
        environment = Environment(Path("aPath"), "aName", "anotherPath")

        self.micromamba.create(environment)

        create_environment_from_file_mock.assert_called_once_with(
            Path("aPath"), "anotherPath"
        )
        create_environment_mock.assert_not_called()

    @patch("album.environments.controller.conda_manager.CondaManager.create_environment")
    @patch(
        "album.environments.controller.conda_manager.CondaManager.create_environment_from_file"
    )
    def test_create_no_yaml(
            self, create_environment_from_file_mock, create_environment_mock
    ):
        environment = Environment(None, "aName", "aPath")
        self.micromamba.create(environment, None)

        create_environment_mock.assert_called_once_with("aPath", None)
        create_environment_from_file_mock.assert_not_called()

    @patch(
        "album.environments.controller.conda_manager.CondaManager.create_or_update_env",
        return_value="Called",
    )
    def test_install(self, create_mock):
        environment = Environment(None, "aName", "aPath")

        self.micromamba.install(environment, "TestVersion")

        create_mock.assert_called_once_with(environment, "TestVersion")


if __name__ == "__main__":
    unittest.main()
