import unittest.suite
from unittest.mock import patch

from album.environments.model.environment import Environment


class TestEnvironment(unittest.TestCase):
    test_environment_name = "unittest"

    def setUp(self):
        super().setUp()

        """Setup things necessary for all tests of this class"""
        self.environment = Environment(None, self.test_environment_name)

    def test_init_(self):
        e = Environment(None, self.test_environment_name)
        self.assertIsNotNone(e)
        self.assertEqual(self.test_environment_name, e.name())
        self.assertIsNone(e.yaml_file())


if __name__ == "__main__":
    unittest.main()
