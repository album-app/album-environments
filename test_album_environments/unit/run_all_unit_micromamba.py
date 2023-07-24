import time
import unittest

from test_album_environments.unit.environments.controller import (
    test_micromamba_manager,
    test_environment_handler,
)
from test_album_environments.unit.environments.model import (
    test_environment,
)
from test_album_environments.unit.environments.utils import test_subcommand
from test_album_environments.unit.environments.utils import (
    test_url_operations,
    test_file_operations,
)


def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromModule(test_micromamba_manager))
    suite.addTests(loader.loadTestsFromModule(test_environment_handler))
    suite.addTests(loader.loadTestsFromModule(test_environment))
    suite.addTests(loader.loadTestsFromModule(test_subcommand))
    suite.addTests(loader.loadTestsFromModule(test_file_operations))
    suite.addTests(loader.loadTestsFromModule(test_url_operations))

    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(suite)
    if result.wasSuccessful():
        time.sleep(5)
        print("Success")
        exit(0)
    else:
        print("Failed")
        exit(1)


main()
