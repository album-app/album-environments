import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from album.environments.controller.package_manager import _is_activation_hint
from album.environments.initialization import PackageManagerHandler
from album.environments.model.environment import Environment
from album.environments.utils.subcommand import SubProcessError
from test_album_environments.test_common import TestCommon

PRIVATE_PROC_DIR_SETTING = "ENVIRONMENT_MICROMAMBA_RUN_PRIVATE_PROC_DIR"  # documented in the CHANGELOG


class TestMicromambaManager(TestCommon):
    test_environment_name = "unittest"

    def setUp(self):
        super().setUp()
        self.test_base = Path(self.test_base_dir.name)
        self.test_environment_path = self.test_base_envs.joinpath(self.test_environment_name)

        if "ENVIRONMENT_DEBUGGING_CONDA_PATH" in os.environ.keys():
            if os.environ["ENVIRONMENT_DEBUGGING_CONDA_PATH"]:
                del os.environ["ENVIRONMENT_DEBUGGING_CONDA_PATH"]

        if "ENVIRONMENT_DEBUGGING_MAMBA_PATH" in os.environ.keys():
            if os.environ.get("ENVIRONMENT_DEBUGGING_MAMBA_PATH"):
                del os.environ["ENVIRONMENT_DEBUGGING_MAMBA_PATH"]

        # ensure no env vars are set
        self.assertIsNotNone(os.environ.get("ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"))
        self.assertIsNone(os.environ.get("ENVIRONMENT_DEBUGGING_MAMBA_PATH"))
        self.assertIsNone(os.environ.get("ENVIRONMENT_DEBUGGING_CONDA_PATH"))

        self.assertTrue(Path(os.environ.get("ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH")).exists())

        package_manager_handler = PackageManagerHandler(
            base_env_path=str(self.test_base_envs),
            installation_path=str(Path(self.test_base_dir.name)),
            micromamba_path=os.environ.get("ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH"),
            mamba_path=None,
            conda_path=None,
            conda_lock_path=None,
        )
        self.micromamba = package_manager_handler.get_package_manager()
        self.assertEqual("micromamba", self.micromamba.get_package_manager_name())

    def tearDown(self) -> None:
        if self.micromamba.environment_exists(self.test_environment_path):
            self.micromamba.remove_environment(self.test_environment_path)
            self.assertFalse(
                self.micromamba.environment_exists(self.test_environment_path)
            )
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
        res = self.micromamba.get_environment_list()

        self.assertListEqual(expected, res)

    @patch("album.environments.controller.package_manager.PackageManager.get_environment_list")
    def test_environment_exists(self, ged_mock):
        target = self.test_base_envs.joinpath("envName1")
        target_not_existing = self.test_base_envs.joinpath("notExitendEnvs")
        Path(target).joinpath("whatever").mkdir(parents=True)

        ged_mock.return_value = [target.resolve()]

        self.assertTrue(self.micromamba.environment_exists(target))
        self.assertFalse(self.micromamba.environment_exists(target_not_existing))

    @patch("album.environments.controller.package_manager.PackageManager.get_info")
    def test_get_active_environment_name(self, ginfo_mock):
        ginfo_mock.return_value = {"environment": "envName1"}
        self.assertEqual("envName1", self.micromamba.get_active_environment_name())

    @patch("album.environments.controller.package_manager.PackageManager.get_info")
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
- conda-forge
dependencies:
- python"""
        with open(self.test_base.joinpath("env_file.yml"), "w") as f:
            f.writelines(env_file)
        self.micromamba.create_environment_from_file(
            self.test_base.joinpath("env_file.yml"), self.test_environment_path
        )
        self.assertTrue(self.micromamba.environment_exists(self.test_environment_path))

    def test_create_environment_from_file_invalid(self):
        # wrong file ending
        with self.assertRaises(NameError):
            self.micromamba.create_environment_from_file(
                self.test_base.joinpath("env.tiff"), self.test_environment_path
            )

    def test_create_environment_from_file_valid_but_empty(self):
        t = self.test_base.joinpath("%s.yml" % self.test_environment_name)
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
            unittest.skip("WARNING - MICROMAMBA ERROR!")

    @patch("album.environments.utils.subcommand.run")
    def test_create_environment_activation_hint_at_debug(self, run_mock):
        self.micromamba.create_environment(self.test_environment_path)

        # the output of creating the environment is logged, the activation hint at DEBUG
        run_mock.assert_called_once()
        self.assertTrue(run_mock.call_args.kwargs["log_output"])
        self.assertIs(_is_activation_hint, run_mock.call_args.kwargs["debug_from"])

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

    @patch("album.environments.controller.package_manager.PackageManager.list_environment")
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

        # generally, test whether python is installed
        self.assertTrue(self.micromamba.is_installed(environment.path(), "python"))

        # we test for minimal package version that is available.
        self.assertTrue(self.micromamba.is_installed(environment.path(), "python", min_package_version="3.9.5"))
        self.assertFalse(self.micromamba.is_installed(environment.path(), "python", min_package_version="500.1"))
        self.assertTrue(self.micromamba.is_installed(environment.path(), "python", min_package_version="2.7"))

        # testing for exact package version
        self.assertTrue(self.micromamba.is_installed(environment.path(), "python", package_version="3.9.5"))
        self.assertFalse(self.micromamba.is_installed(environment.path(), "python", package_version="3.9.4"))

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

    def _run_script_capturing_call(self, run_mock, environment_variables, platform="linux", setting=None):
        """Call run_script with a mocked subprocess; return (args, env, registry dir existed during the call)."""
        seen = {}

        def _run(args, pipe_output, env):
            seen["registry_existed"] = env is not None and os.path.isdir(env.get("XDG_CACHE_HOME", ""))

        run_mock.side_effect = _run
        environment = Environment(None, "aName", "aPath")
        with patch.object(sys, "platform", platform), patch.dict(os.environ):
            os.environ.pop(PRIVATE_PROC_DIR_SETTING, None)
            if setting is not None:
                os.environ[PRIVATE_PROC_DIR_SETTING] = setting
            self.micromamba.run_script(
                environment, "script.py", environment_variables=environment_variables, argv=["script.py", "--a=1"]
            )
        run_mock.assert_called_once()
        return run_mock.call_args[0][0], run_mock.call_args[1]["env"], seen["registry_existed"]

    def _expected_run_args(self, *wrapper):
        return [
            self.micromamba.get_install_environment_executable(), "run", "--prefix", os.path.normpath("aPath"),
            *wrapper, "python", "-u", os.path.normpath("script.py"), "--a=1",
        ]

    @patch("album.environments.utils.subcommand.run")
    def test_run_script_private_proc_dir(self, run_mock):
        # album#227: parallel "micromamba run" calls must not share (and lock) ~/.cache/mamba/proc
        caller_env = {"FOO": "bar"}

        args, env, registry_existed = self._run_script_capturing_call(run_mock, caller_env)

        # micromamba gets a private registry that exists during the run and is removed afterwards
        self.assertTrue(registry_existed)
        self.assertFalse(os.path.exists(env["XDG_CACHE_HOME"]))
        # the solution's command gets the caller's (unset) XDG_CACHE_HOME back
        self.assertEqual(self._expected_run_args("env", "-u", "XDG_CACHE_HOME"), args)
        self.assertEqual("bar", env["FOO"])
        self.assertEqual({"FOO": "bar"}, caller_env)  # caller's mapping is not modified

    @patch("album.environments.utils.subcommand.run")
    def test_run_script_private_proc_dir_keeps_caller_cache_home(self, run_mock):
        caller_env = {"FOO": "bar", "XDG_CACHE_HOME": "/home/me/my cache"}

        args, env, registry_existed = self._run_script_capturing_call(run_mock, caller_env)

        self.assertTrue(registry_existed)
        self.assertNotEqual("/home/me/my cache", env["XDG_CACHE_HOME"])
        self.assertEqual(self._expected_run_args("env", "XDG_CACHE_HOME=/home/me/my cache"), args)
        self.assertEqual("/home/me/my cache", caller_env["XDG_CACHE_HOME"])

    @patch("album.environments.utils.subcommand.run")
    def test_run_script_private_proc_dir_inherits_os_environ(self, run_mock):
        with patch.dict(os.environ, {"ENVIRONMENT_TEST_INHERITED": "inherited"}):
            os.environ.pop("XDG_CACHE_HOME", None)
            args, env, registry_existed = self._run_script_capturing_call(run_mock, None)

        self.assertTrue(registry_existed)
        self.assertEqual("inherited", env["ENVIRONMENT_TEST_INHERITED"])
        self.assertEqual(self._expected_run_args("env", "-u", "XDG_CACHE_HOME"), args)

    @patch("album.environments.utils.subcommand.run")
    def test_run_script_private_proc_dir_removed_on_failure(self, run_mock):
        registries = []

        def _run(args, pipe_output, env):
            registries.append(env["XDG_CACHE_HOME"])
            raise SubProcessError(1, "failed")

        run_mock.side_effect = _run
        environment = Environment(None, "aName", "aPath")
        with patch.object(sys, "platform", "linux"), patch.dict(os.environ):
            os.environ.pop(PRIVATE_PROC_DIR_SETTING, None)
            with self.assertRaises(SubProcessError):
                self.micromamba.run_script(environment, "script.py", environment_variables={})

        self.assertEqual(1, len(registries))
        self.assertFalse(os.path.exists(registries[0]))

    @patch("album.environments.utils.subcommand.run")
    def test_run_script_private_proc_dir_disabled(self, run_mock):
        for setting in ["0", "false", "No", " off "]:
            run_mock.reset_mock()
            caller_env = {"FOO": "bar"}

            args, env, _ = self._run_script_capturing_call(run_mock, caller_env, setting=setting)

            self.assertEqual(self._expected_run_args(), args)
            self.assertIs(caller_env, env)

    @patch("album.environments.utils.subcommand.run")
    def test_run_script_private_proc_dir_not_on_windows(self, run_mock):
        caller_env = {"FOO": "bar"}

        args, env, _ = self._run_script_capturing_call(run_mock, caller_env, platform="win32")

        self.assertNotIn("env", args)
        self.assertIs(caller_env, env)

    @patch("album.environments.utils.subcommand.run")
    def test_run_script_private_proc_dir_solution_argument_named_prefix(self, run_mock):
        # the solution's own "--prefix" argument must not move the wrapper
        environment = Environment(None, "aName", "aPath")
        with patch.object(sys, "platform", "linux"), patch.dict(os.environ):
            os.environ.pop(PRIVATE_PROC_DIR_SETTING, None)
            self.micromamba.run_script(
                environment, "script.py", environment_variables={}, argv=["script.py", "--prefix", "out"]
            )

        self.assertEqual(
            [
                self.micromamba.get_install_environment_executable(), "run", "--prefix", os.path.normpath("aPath"),
                "env", "-u", "XDG_CACHE_HOME", "python", "-u", os.path.normpath("script.py"), "--prefix", "out",
            ],
            run_mock.call_args[0][0],
        )

    @patch("album.environments.utils.subcommand.run")
    def test_run_script_private_proc_dir_unexpected_call_layout(self, run_mock):
        # a call that does not have the layout of _get_run_script_args is run unchanged, never wrapped at a guess
        caller_env = {"FOO": "bar"}
        unexpected_call = ["micromamba", "run", "-p", "aPath", "python", "script.py", "--prefix", "out"]
        with patch.object(sys, "platform", "linux"), patch.dict(os.environ):
            os.environ.pop(PRIVATE_PROC_DIR_SETTING, None)
            self.micromamba._run_script_process(list(unexpected_call), caller_env, True)

        run_mock.assert_called_once_with(unexpected_call, pipe_output=True, env=caller_env)
        self.assertIs(caller_env, run_mock.call_args[1]["env"])
        self.assertIn("Unexpected micromamba call", self.captured_output.getvalue())

    @staticmethod
    def _make_private_proc_dir(parent, name, proc_files=None, modified_seconds_ago=0):
        """Create <parent>/<name>, with mamba/proc/<proc_files> unless proc_files is None, and set its mtimes."""
        path = parent.joinpath(name)
        directories = [path]
        if proc_files is None:
            path.mkdir()
        else:
            proc_dir = path.joinpath("mamba", "proc")
            proc_dir.mkdir(parents=True)
            for file_name in proc_files:
                proc_dir.joinpath(file_name).touch()
            directories = [proc_dir, proc_dir.parent, path]
        modified = time.time() - modified_seconds_ago
        for directory in directories:
            os.utime(directory, (modified, modified))
        return path

    @patch("album.environments.utils.subcommand.run")
    def test_run_script_removes_leftover_private_proc_dirs(self, run_mock):
        # interrupted runs (Ctrl-C, SIGTERM, SIGKILL) leave their private registry behind; the next run removes it
        tmp_dir = Path(self.test_base_dir.name).joinpath("tmp")
        tmp_dir.mkdir()
        two_hours = 2 * 3600
        interrupted = self._make_private_proc_dir(
            tmp_dir, "album-micromamba-run-interrupted", ["proc.lock"], two_hours
        )
        never_started = self._make_private_proc_dir(tmp_dir, "album-micromamba-run-never-started", None, two_hours)
        running = self._make_private_proc_dir(
            tmp_dir, "album-micromamba-run-running", ["proc.lock", "4242.json"], two_hours
        )
        recent = self._make_private_proc_dir(tmp_dir, "album-micromamba-run-recent", ["proc.lock"], 60)
        just_finished = self._make_private_proc_dir(
            tmp_dir, "album-micromamba-run-just-finished", ["proc.lock"], two_hours
        )
        os.utime(just_finished.joinpath("mamba", "proc"))  # its <pid>.json was deleted a moment ago
        other_name = self._make_private_proc_dir(tmp_dir, "other-run", ["proc.lock"], two_hours)
        not_a_dir = tmp_dir.joinpath("album-micromamba-run-file")
        not_a_dir.touch()
        os.utime(not_a_dir, (time.time() - two_hours, time.time() - two_hours))

        with patch.object(tempfile, "tempdir", str(tmp_dir)):
            _, env, registry_existed = self._run_script_capturing_call(run_mock, {})

        self.assertTrue(registry_existed)
        self.assertEqual(tmp_dir, Path(env["XDG_CACHE_HOME"]).parent)
        self.assertEqual(
            sorted(path.name for path in [running, recent, just_finished, other_name, not_a_dir]),
            sorted(os.listdir(tmp_dir)),
        )
        self.assertFalse(interrupted.exists())
        self.assertFalse(never_started.exists())

    @patch("album.environments.utils.subcommand.run")
    def test_run_script_keeps_private_proc_dirs_of_other_users(self, run_mock):
        tmp_dir = Path(self.test_base_dir.name).joinpath("tmp")
        tmp_dir.mkdir()
        leftover = self._make_private_proc_dir(tmp_dir, "album-micromamba-run-leftover", ["proc.lock"], 2 * 3600)
        real_stat = os.stat

        def _stat_own_registry_as_other_user(path, *args, **kwargs):
            result = real_stat(path, *args, **kwargs)
            if Path(path).parent == tmp_dir and Path(path) != leftover:
                values = list(result)
                values[4] += 1  # st_uid
                return os.stat_result(values)
            return result

        with patch.object(tempfile, "tempdir", str(tmp_dir)), patch.object(
            os, "stat", _stat_own_registry_as_other_user
        ):
            self._run_script_capturing_call(run_mock, {})

        self.assertEqual([leftover.name], os.listdir(tmp_dir))

    def test_create_or_update_env_no_env(self):
        update_mock = MagicMock()
        create_mock = MagicMock()
        self.micromamba.update = update_mock
        self.micromamba.create = create_mock
        environment = Environment(None, "aName", "aPath")

        self.micromamba.create_or_update_env(environment, None)

        create_mock.assert_called_once_with(environment, None)
        update_mock.assert_not_called()

    @patch("album.environments.controller.package_manager.PackageManager.create")
    @patch("album.environments.controller.package_manager.PackageManager.update")
    @patch("album.environments.controller.package_manager.PackageManager.environment_exists")
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

    @patch("album.environments.controller.package_manager.PackageManager.create_environment")
    @patch(
        "album.environments.controller.package_manager.PackageManager.create_environment_from_file"
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

    @patch("album.environments.controller.package_manager.PackageManager.create_environment")
    @patch(
        "album.environments.controller.package_manager.PackageManager.create_environment_from_file"
    )
    def test_create_no_yaml(
            self, create_environment_from_file_mock, create_environment_mock
    ):
        environment = Environment(None, "aName", "aPath")
        self.micromamba.create(environment, None)

        create_environment_mock.assert_called_once_with("aPath", None)
        create_environment_from_file_mock.assert_not_called()

    @patch(
        "album.environments.controller.package_manager.PackageManager.create_or_update_env",
        return_value="Called",
    )
    def test_install(self, create_mock):
        environment = Environment(None, "aName", "aPath")

        self.micromamba.install(environment, "TestVersion")

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
        self.assertEqual("3.9.5", self.micromamba.get_package_version(Path("aPath"), "python"))


class TestActivationHint(unittest.TestCase):
    def test_is_activation_hint(self):
        # the first line of the hint of micromamba 1.x and 2.x, and of conda and mamba 1.x
        for line in [
            "To activate this environment, use:",
            "To activate this environment, use",
            "# To activate this environment, use",
        ]:
            self.assertTrue(_is_activation_hint(line), line)
        for line in [
            "Transaction finished",
            "  + python  3.10.14  h955ad1f_0_cpython  conda-forge  Cached",
            "#",
            "    micromamba activate /path/to/env",
        ]:
            self.assertFalse(_is_activation_hint(line), line)
