import logging
import os
import sys
import unittest

from album.runner.album_logging import get_active_logger
from test_album_environments.global_exception_watcher import GlobalExceptionWatcher


class TestCommon(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.logger = get_active_logger()
        self.enable_test_logging()

    def enable_test_logging(self):
        if os.getenv("ALBUM_TEST_LOGGING", "False") == "True":
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel("DEBUG")
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel("DEBUG")
            self.logger.debug("Test logging enabled!")

    def run(self, result=None):
        # add watcher to catch any exceptions thrown in threads
        with GlobalExceptionWatcher():
            super(TestCommon, self).run(result)
