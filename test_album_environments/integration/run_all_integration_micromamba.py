import time
import unittest

from test_album_environments.integration.environments import (
    test_integration_conda_lock_micromamba,
    test_integration_env_creation_micromamba,
)


def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromModule(test_integration_conda_lock_micromamba))
    suite.addTests(loader.loadTestsFromModule(test_integration_env_creation_micromamba))

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
