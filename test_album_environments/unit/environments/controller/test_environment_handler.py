import unittest.mock

from album.environments.controller.environment_handler import EnvironmentHandler


class TestEnvironmentManager(unittest.TestCase):
    def setUp(self):
        super().setUp()
        #FIXME
        self.environment_manager = EnvironmentHandler()

    def tearDown(self) -> None:
        super().tearDown()

    @unittest.skip("Needs to be implemented!")
    def test_install_environment(self):
        # ToDo: implement!
        pass

    @unittest.skip("Needs to be implemented!")
    def test_run_script(self):
        # ToDo: implement!
        pass

    @unittest.skip("Needs to be implemented!")
    def test_get_package_manager(self):
        # ToDo: implement!
        pass

    @unittest.skip("Needs to be implemented!")
    def test__prepare_env_file(self):
        # ToDo: implement!
        pass

    @unittest.skip("Needs to be implemented!")
    def test_get_installed_package_manager(self):
        # ToDo: implement!
        pass

    @unittest.skip("Needs to be implemented!")
    def test_check_for_executable(self):
        # ToDo: implement!
        pass

    @unittest.skip("Needs to be implemented!")
    def test_build_conda_executable(self):
        # ToDo: implement!
        pass
