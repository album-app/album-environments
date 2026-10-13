import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from album.environments.api.environment_api import IEnvironmentAPI
from album.environments.environment_api import EnvironmentAPI
from album.environments.initialization import PackageManagerHandler
from album.environments.model.environment import Environment
from test_album_environments.integration.environments.test_integration_conda_lock_base import (
    _TestIntegrationCondaLock,
)


class TestIntegrationCondaLockMicromamba(_TestIntegrationCondaLock):
    test_environment_name = "micromamba_test_environment"

    def init_env_handler(self) -> IEnvironmentAPI:
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

        # uses micromamba from CICD path
        return EnvironmentAPI(
            package_manager_handler.get_package_manager(),
            package_manager_handler.get_conda_lock_manager(),
        )

    def test_create_conda_lockfile(self):
        super().create_conda_lockfile()

    def test_create_remove_environment(self):
        super().create_remove_environment()

    def test_create_environment_from_file_and_get_package_version(self):
        super().create_environment_from_file_and_get_package_version()

    def test_run_script(self):
        super().run_script()

    @unittest.skipIf(
        sys.platform in ("win32", "cygwin"), "micromamba does not lock its process registry on Windows"
    )
    def test_run_script_private_proc_dir(self):
        # album#227: "micromamba run" must not use the shared, locked process registry
        # <XDG_CACHE_HOME>/mamba/proc, while the solution still sees the caller's XDG_CACHE_HOME
        package_manager = self.env_handler.get_package_manager()
        package_manager.create_environment(str(self.test_environment_path))
        user_cache = Path(self.test_base_dir.name).joinpath("user_cache")
        script_path = Path(self.test_base_dir.name).joinpath("print_cache_home.py")
        script_path.write_text("import os; print('cache_home=%s' % os.environ.get('XDG_CACHE_HOME'))")
        environment = Environment(None, self.test_environment_name, self.test_environment_path)

        with patch.dict(os.environ):
            os.environ.pop("ENVIRONMENT_MICROMAMBA_RUN_PRIVATE_PROC_DIR", None)
            caller_env = os.environ.copy()
            caller_env["XDG_CACHE_HOME"] = str(user_cache)
            package_manager.run_script(environment, str(script_path), environment_variables=caller_env)

            self.assertIn("cache_home=%s" % user_cache, self.captured_output.getvalue())
            self.assertFalse(user_cache.joinpath("mamba", "proc").exists())

            del caller_env["XDG_CACHE_HOME"]
            package_manager.run_script(environment, str(script_path), environment_variables=caller_env)

            self.assertIn("cache_home=None", self.captured_output.getvalue())
