import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path

from album.runner.album_logging import get_active_logger

from test_album_environments.global_exception_watcher import GlobalExceptionWatcher


class TestCommon(unittest.TestCase):
    test_environment_name = "unittest"

    def setUp(self) -> None:
        super().setUp()
        self.test_base_dir = tempfile.TemporaryDirectory()
        self.test_base_envs = Path(self.test_base_dir.name).joinpath("envs")
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
            super().run(result)
