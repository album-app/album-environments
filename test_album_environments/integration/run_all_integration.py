import time
import unittest

from test_album_environments.integration.environments import test_integration_env_creation, test_conda_lock


def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromModule(test_integration_env_creation))
    suite.addTests(loader.loadTestsFromModule(test_conda_lock))

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
