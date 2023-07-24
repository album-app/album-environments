import time
import unittest

from test_album_environments.unit.environments.controller import (
    test_conda_manager,
    test_environment_handler,
)


def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromModule(test_conda_manager))
    suite.addTests(loader.loadTestsFromModule(test_environment_handler))

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
