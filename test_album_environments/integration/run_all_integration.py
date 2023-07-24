import time
import unittest


def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # suite.addTests(loader.loadTestsFromModule(test_integration_deploy))

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
