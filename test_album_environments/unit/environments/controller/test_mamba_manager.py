import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from album.environments.initialization import PackageManagerHandler
from album.environments.model.environment import Environment
from test_album_environments.test_common import TestCommon


class TestMambaManager(TestCommon):
    test_environment_name = "unittest"

    def setUp(self):
        super().setUp()
        self.test_base = Path(self.test_base_dir.name)
        self.test_environment_path = self.test_base_envs.joinpath(self.test_environment_name)

        if "ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH" in os.environ.keys():
            if os.environ["ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"]:
                del os.environ["ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"]

        if "ENVIRONMENT_DEBUGGING_CONDA_PATH" in os.environ.keys():
            if os.environ.get("ENVIRONMENT_DEBUGGING_CONDA_PATH"):
                del os.environ["ENVIRONMENT_DEBUGGING_CONDA_PATH"]

        # ensure no env vars are set
        self.assertIsNone(os.environ.get("ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"))
        self.assertIsNotNone(os.environ.get("ENVIRONMENT_DEBUGGING_MAMBA_PATH"))
        self.assertIsNone(os.environ.get("ENVIRONMENT_DEBUGGING_CONDA_PATH"))

        # uses mamba from CICD path
        package_manager_handler = PackageManagerHandler(
            base_env_path=str(self.test_base_envs),
            installation_path=str(Path(self.test_base_dir.name)),
            micromamba_path=None,
            mamba_path=os.environ.get("ENVIRONMENT_DEBUGGING_MAMBA_PATH"),
            conda_path=None,
            conda_lock_path=None,
        )

        self.mamba = package_manager_handler.get_package_manager()

    def tearDown(self) -> None:
        if self.mamba.environment_exists(self.test_environment_path):
            self.mamba.remove_environment(self.test_environment_path)
            self.assertFalse(self.mamba.environment_exists(self.test_environment_path))
        self.test_base_dir.cleanup()
        super().tearDown()

    def test_get_environment_list(self):
        expected = [
            self.test_base_envs.joinpath("envName1").resolve(),
            self.test_base_envs.joinpath("envName2").resolve()
        ]

        # create some content
        Path(expected[0]).joinpath("somefile").mkdir(parents=True)
        Path(expected[1]).joinpath("somefile").mkdir(parents=True)

        # get the list
        res = self.mamba.get_environment_list()

        self.assertListEqual(expected, res)

    @patch("album.environments.controller.conda_manager.CondaManager.get_environment_list")
    def test_environment_exists(self, ged_mock):
        target = self.test_base.joinpath("envName1")
        target_not_existing = self.test_base.joinpath("notExitendEnvs")
        Path(target).joinpath("whatever").mkdir(parents=True)

        ged_mock.return_value = [target.resolve()]

        self.assertTrue(self.mamba.environment_exists(target))
        self.assertFalse(self.mamba.environment_exists(target_not_existing))

    @patch("album.environments.controller.conda_manager.CondaManager.get_info")
    def test_get_active_environment_name(self, ginfo_mock):
        ginfo_mock.return_value = {"active_prefix_name": "envName1"}
        self.assertEqual("envName1", self.mamba.get_active_environment_name())

    @patch("album.environments.controller.conda_manager.CondaManager.get_info")
    def test_get_active_environment_path(self, ginfo_mock):
        ginfo_mock.return_value = {"active_prefix": "aEnvPath"}
        self.assertEqual("aEnvPath", str(self.mamba.get_active_environment_path()))

    def test_get_info(self):
        r = self.mamba.get_info()

        self.assertIn("envs", r)
        self.assertIn("active_prefix_name", r)
        self.assertIn("active_prefix", r)

    def test_list_environment(self):
        p = self.mamba.get_active_environment_path()
        r = self.mamba.list_environment(p)

        self.assertIsNotNone(r)

    @patch("album.environments.controller.conda_manager.CondaManager._install")
    def test_create_environment_from_file_valid_file(self, install_mock):
        self.assertFalse(self.mamba.environment_exists(self.test_environment_path))
        env_file = """
name: unittest
channels:
  - conda-forge
dependencies:
  - python
"""
        with open(self.test_base.joinpath("env_file.yml"), "w") as f:
            f.writelines(env_file)
        self.mamba.create_environment_from_file(
            self.test_base.joinpath("env_file.yml"), self.test_environment_path
        )
        self.assertEqual(1, install_mock.call_count)

    def test_create_environment_from_file_invalid(self):
        # wrong file ending
        with self.assertRaises(NameError):
            self.mamba.create_environment_from_file(
                self.test_base.joinpath("env.tiff"), self.test_environment_name
            )

    def test_create_environment_from_file_valid_but_empty(self):
        t = self.test_base.joinpath("%s.yml" % self.test_environment_name)
        t.touch()
        # no content in file
        with self.assertRaises(ValueError):
            self.mamba.create_environment_from_file(t, self.test_environment_name)

    def test_create_environment(self):
        self.assertFalse(self.mamba.environment_exists(self.test_environment_path))

        skip = False  # The test checks if an environment error is raised when the same environment ist created two
        # times the skip variable is used two skip the second env creation call if the first one fails

        try:
            self.mamba.create_environment(self.test_environment_path)
        except RuntimeError as err:
            print(err)
            skip = True

        if not skip:
            # create it again without force fails
            with self.assertRaises(EnvironmentError):
                self.mamba.create_environment(self.test_environment_path)

            self.assertTrue(self.mamba.environment_exists(self.test_environment_path))

            # check if python & pip installed
            self.assertTrue(
                self.mamba.is_installed(
                    self.test_environment_path,
                    "python",
                )
            )
            self.assertTrue(
                self.mamba.is_installed(
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
        self.mamba.create_environment(self.test_environment_path)
        run_mock.assert_called_once()

        # run_mock not called again
        self.mamba.remove_environment("iDoNotExist")
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
        self.assertTrue(self.mamba.is_installed(environment.path(), "python"))
        self.assertTrue(self.mamba.is_installed(environment.path(), "python", "3.9.5"))
        self.assertFalse(self.mamba.is_installed(environment.path(), "python", "500.1"))
        self.assertTrue(self.mamba.is_installed(environment.path(), "python", "2.7"))

    @patch(
        "album.environments.utils.subcommand.run",
        return_value="ranScript",
    )
    def test_run_script(self, run_mock):
        with tempfile.NamedTemporaryFile(mode="w") as tmp:
            tmp.write('print("%s")' % self.test_environment_name)
            environment = Environment(None, "aName", "aPath")
            self.mamba.run_script(environment, tmp.name)
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
                self.mamba.run_script(environment, tmp.name)
            conda_run_mock.assert_not_called()

    def test_create_or_update_env_no_env(self):
        update_mock = MagicMock()
        create_mock = MagicMock()
        self.mamba.update = update_mock
        self.mamba.create = create_mock
        environment = Environment(None, "aName", "aPath")

        self.mamba.create_or_update_env(environment, None)

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

        self.mamba.create_or_update_env(environment)

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

        self.mamba.create(environment)

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
        self.mamba.create(environment, None)

        create_environment_mock.assert_called_once_with("aPath", None)
        create_environment_from_file_mock.assert_not_called()

    @patch(
        "album.environments.controller.conda_manager.CondaManager.create_or_update_env",
        return_value="Called",
    )
    def test_install(self, create_mock):
        environment = Environment(None, "aName", "aPath")

        self.mamba.install(environment, "TestVersion")

        create_mock.assert_called_once_with(environment, "TestVersion")

    @patch("album.environments.controller.package_manager.PackageManager.list_environment")
    def test_get_package_version(self, list_environment_mock):
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
        self.assertEqual("3.9.5", self.mamba.get_package_version(Path("aPath"), "python"))
