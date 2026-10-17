import logging
import os
import sys
import tempfile
import threading
import time
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from album.environments.utils import subcommand
from album.environments.utils.subcommand import LogfileBuffer, SubProcessError
from album.runner import album_logging
from album.runner.album_logging import (
    get_active_logger,
    get_active_logger_in_thread,
    pop_active_logger,
    push_active_logger,
)

# writes "step 0" to "step 2" as progress updates, then the line "step 3"
PROGRESS_SCRIPT = (
    "import sys\n"
    "for i in range(3):\n"
    "    sys.stdout.write('\\rstep %d' % i)\n"
    "    sys.stdout.flush()\n"
    "print('\\rstep 3')\n"
    "print('done')\n"
)


class TestSubcommand(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.tmp_dir_obj = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self.tmp_dir_obj.name)
        self.captured_output = StringIO()
        self.logger = get_active_logger()
        self.logger.handlers.clear()
        self.logger.name = "test-logger"
        self.logger.setLevel("INFO")
        ch = logging.StreamHandler(self.captured_output)
        ch.setLevel("INFO")
        self.logger.addHandler(ch)

    def tearDown(self) -> None:
        self.tmp_dir_obj.cleanup()
        super().tearDown()

    @unittest.skip("Fixme!")
    def test_run(self):
        with self.assertLogs(self.logger, level="DEBUG") as cm:
            # call
            subcommand.run(["echo", "test"])

            sys.stdout.flush()
            time.sleep(0.5)
            print("")
            # assert
            self.assertTrue(len(cm.output) > 1)
            self.assertTrue(cm.output[0].endswith("Running command: echo test..."))
            self.assertTrue(cm.output[1].endswith("test"))

    def test_run_python(self):
        with self.assertLogs(self.logger, level="DEBUG") as cm:
            fd, path = tempfile.mkstemp()
            try:
                with os.fdopen(fd, "w") as tmp:
                    tmp.write("print('nothing happening')\n")
                subcommand.run(["python", path])
            finally:
                os.remove(path)

            time.sleep(0.2)

            self.assertEqual(2, len(cm.output))
            self.assertTrue(
                cm.output[0].endswith("Running command: python %s..." % path)
            )
            self.assertTrue(cm.output[1].endswith("nothing happening"))

    def test_run_throw_error(self):

        with self.assertLogs(self.logger, level="DEBUG") as cm:
            fd, path = tempfile.mkstemp()
            try:
                with os.fdopen(fd, "w") as tmp:
                    tmp.write("raise RuntimeError('this should not happen')\n")
                with self.assertRaises(SubProcessError):
                    subcommand.run(["python", path])
            finally:
                os.remove(path)
                sys.stderr.flush()
                sys.stdout.flush()

            time.sleep(0.2)
            self.assertEqual(5, len(cm.output))
            self.assertIn("Running command: python %s..." % path, cm.output[0])
            self.assertIn("Traceback", cm.output[1])
            self.assertIn("RuntimeError: this should not happen", cm.output[4])

    def test_run_print_to_stderr(self):
        with self.assertLogs(self.logger, level="DEBUG") as cm:

            fd, path = tempfile.mkstemp()
            try:
                with os.fdopen(fd, "w") as tmp:
                    tmp.write(
                        "import sys\nprint('this should not happen', file = sys.stderr)\n"
                    )
                subcommand.run(["python", path])
            finally:
                os.remove(path)

            time.sleep(0.2)
            self.assertEqual(2, len(cm.output))
            self.assertTrue(
                cm.output[0].endswith("Running command: python %s..." % path)
            )
            self.assertTrue(cm.output[1].endswith("this should not happen"))

    def test_run_debug_from(self):
        """Plain lines from the first line debug_from matches on are logged at DEBUG."""
        fd, path = tempfile.mkstemp(suffix=".py")
        try:
            with os.fdopen(fd, "w") as tmp:
                tmp.write(
                    "print('Transaction finished')\n"
                    "print('To activate this environment, use:')\n"
                    "print('    micromamba activate /some/env')\n"
                    "print('WARNING: a warning after the hint')\n"
                )
            with self.assertLogs(self.logger, level="DEBUG") as cm:
                subcommand.run(
                    [sys.executable, path],
                    debug_from=lambda line: line.startswith("To activate"),
                )
        finally:
            os.remove(path)

        levels = {r.getMessage().strip(): r.levelname for r in cm.records}
        self.assertEqual("INFO", levels["Transaction finished"])
        self.assertEqual("DEBUG", levels["To activate this environment, use:"])
        self.assertEqual("DEBUG", levels["micromamba activate /some/env"])
        # a line in a log format keeps its level
        self.assertEqual("WARNING", levels["a warning after the hint"])

    def test_run_progress(self):
        """A line the process redraws with a lone carriage return is a progress update."""
        with patch.object(subcommand, "PROGRESS_INTERVAL", 0):
            records = self._run_python(PROGRESS_SCRIPT)

        # the blank update before "step 0" is dropped
        self.assertEqual(
            [
                ("step 0", True),
                ("step 1", True),
                ("step 2", True),
                ("step 3", False),
                ("done", False),
            ],
            [(r.getMessage(), getattr(r, "album_progress", False)) for r in records],
        )

    def test_run_progress_interval(self):
        """Progress updates are logged at most once per PROGRESS_INTERVAL, lines always."""
        with patch.object(subcommand, "PROGRESS_INTERVAL", 3600):
            records = self._run_python(PROGRESS_SCRIPT)

        self.assertEqual(
            ["step 0", "step 3", "done"], [r.getMessage() for r in records]
        )

    def test_run_progress_at_end_of_output(self):
        """If the output ends in a redrawn line, its last update is logged as a line."""
        with patch.object(subcommand, "PROGRESS_INTERVAL", 3600):
            records = self._run_python(
                "for i in range(0, 101, 50):\n"
                "    print('progress %d%%' % i, end='\\r', flush=True)\n"
            )

        self.assertEqual(
            [("progress 0%", True), ("progress 100%", False)],
            [(r.getMessage(), getattr(r, "album_progress", False)) for r in records],
        )

    def test_run_progress_cleared_at_end_of_output(self):
        """A redrawn line the process clears before its output ends is not logged again."""
        with patch.object(subcommand, "PROGRESS_INTERVAL", 3600):
            records = self._run_python(
                "print('progress 0%', end='\\r', flush=True)\n"
                "print('progress 100%', end='\\r', flush=True)\n"
                "print(' ' * 13, end='\\r', flush=True)\n"
            )

        self.assertEqual(["progress 0%"], [r.getMessage() for r in records])

    def test_run_undecodable_output(self):
        """Bytes that are not valid in the encoding are replaced, the run goes on."""
        records = self._run_python(
            "import sys\n"
            "sys.stdout.buffer.write(b'caf\\xff\\n')\n"
            "print('done')\n"
        )

        self.assertEqual(["caf�", "done"], [r.getMessage() for r in records])

    def _run_python(self, script):
        """Run the script with subcommand.run, return the log records of its output."""
        fd, path = tempfile.mkstemp(suffix=".py")
        try:
            with os.fdopen(fd, "w") as tmp:
                tmp.write(script)
            with self.assertLogs(self.logger, level="INFO") as cm:
                subcommand.run([sys.executable, path])
        finally:
            os.remove(path)
        return cm.records

    @unittest.skip("Fixme!")
    def test_run_logging_from_thread(self):
        self.logger.setLevel("DEBUG")
        thread = threading.Thread(
            target=self._run_in_thread, args=(threading.current_thread().ident,)
        )
        thread.start()
        thread.join()

    def _run_in_thread(self, parent_thread_id):
        album_logging.configure_logging("thread", parent_thread_id=parent_thread_id)
        self.test_run()


class TestLogfileBuffer(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.captured_output = StringIO()
        self.logger = get_active_logger()
        self.logger.handlers.clear()
        self.logger.name = "test-logger"
        self.logger.setLevel("INFO")
        ch = logging.StreamHandler(self.captured_output)
        ch.setLevel("INFO")
        self.logger.addHandler(ch)

    def tearDown(self) -> None:
        pop_active_logger()
        super().tearDown()

    def test_write(self):
        self.assertIsNotNone(get_active_logger())

        log_buffer = LogfileBuffer(get_active_logger())
        log_buffer.write("app1 - WARNING - message\n over \n several \n lines\n")
        log_buffer.write("DEBUG: - d\nasfasdfsadfasdfasdfsadfasdfasdfasdfasdfw\n")
        log_buffer.write("16:07:16 DEBUG  name: - d\nfghfgh\n")
        log_buffer.write("asfasdfsadfa\ng\napp1 - INFO - i\no\ns\nl\n")

        logs = self.get_logs()
        self.assertIn("app1 - WARNING - message", logs[0])
        self.assertEqual(" over ", logs[1])
        self.assertEqual(" several ", logs[2])
        self.assertIn(" lines", logs[3])
        self.assertIn("asfasdfsadfa", logs[4])
        self.assertEqual("g", logs[5])
        self.assertIn("app1 - INFO - i", logs[6])
        self.assertEqual("o", logs[7])
        self.assertEqual("s", logs[8])
        self.assertIn("l", logs[9])

    @unittest.skipIf(sys.platform == "darwin", "Multiprocessing broken for MACOS!")
    def test_multiprocessing(self):
        for i in range(0, 10):
            capture_output1 = StringIO()
            capture_output2 = StringIO()
            thread1 = threading.Thread(
                target=self.log_in_thread, args=("thread1", capture_output1)
            )
            thread2 = threading.Thread(
                target=self.log_in_thread, args=("thread2", capture_output2)
            )

            thread1.start()
            thread2.start()

            thread1_ident = thread1.ident
            thread2_ident = thread2.ident

            thread1.join()
            thread2.join()

            self.assertFalse(thread1.is_alive())
            self.assertFalse(thread2.is_alive())

            logger1 = get_active_logger_in_thread(thread1_ident)
            logger2 = get_active_logger_in_thread(thread2_ident)

            self.assertIsNotNone(logger1)
            self.assertIsNotNone(logger2)
            self.assertNotEqual(thread1_ident, thread2_ident)
            self.assertNotEqual(logger1, get_active_logger())
            self.assertNotEqual(logger2, get_active_logger())
            self.assertNotEqual(logger1, logger2)

            logs1 = self.as_list(capture_output1.getvalue())
            logs2 = self.as_list(capture_output2.getvalue())

            self.assertEqual(100, len(logs1))
            self.assertEqual(100, len(logs2))
            all(self.assertTrue(elem.startswith("thread1")) for elem in logs1)
            all(self.assertTrue(elem.startswith("thread2")) for elem in logs2)

    def test_parse_log(self):
        log_buffer = LogfileBuffer(get_active_logger())

        res = log_buffer.parse_log("14:15:12 WARNING name - message")
        self.assertEqual("name", res.name)
        self.assertEqual("WARNING", res.level)
        self.assertEqual("message", res.message)

        res = log_buffer.parse_log("14:15:12 WARNING   message")
        self.assertEqual(None, res.name)
        self.assertEqual("WARNING", res.level)
        self.assertEqual("message", res.message)

        res = log_buffer.parse_log("14:15:12 WARNING message")
        self.assertEqual(None, res.name)
        self.assertEqual("WARNING", res.level)
        self.assertEqual("message", res.message)

        res = log_buffer.parse_log("14:15:12 WARNING  ~ message")
        self.assertEqual("~", res.name)
        self.assertEqual("WARNING", res.level)
        self.assertEqual("message", res.message)

        res = log_buffer.parse_log("14:15:12 WARNING  ~~ message")
        self.assertEqual("~~", res.name)
        self.assertEqual("WARNING", res.level)
        self.assertEqual("message", res.message)

        res = log_buffer.parse_log("WARNING root.script - logging warning")
        self.assertEqual("root.script", res.name)
        self.assertEqual("WARNING", res.level)
        self.assertEqual("logging warning", res.message)

        res = log_buffer.parse_log("WARNING name - message")
        self.assertEqual("name", res.name)
        self.assertEqual("WARNING", res.level)
        self.assertEqual("message", res.message)

        res = log_buffer.parse_log("INFO    root.script - message")
        self.assertEqual("root.script", res.name)
        self.assertEqual("INFO", res.level)
        self.assertEqual("message", res.message)

        res = log_buffer.parse_log(
            "15:22:24.487 [SciJava-7e75bf2d-Thread-0] DEBUG message"
        )
        self.assertIsNone(res)

        res = log_buffer.parse_log("[WARNING] message")
        self.assertEqual(None, res.name)
        self.assertEqual("WARNING", res.level)
        self.assertEqual("message", res.message)

        res = log_buffer.parse_log("WARNING: message")
        self.assertEqual(None, res.name)
        self.assertEqual("WARNING", res.level)
        self.assertEqual("message", res.message)

    @staticmethod
    def log_in_thread(name, stream_handler):
        logger = logging.getLogger(name)
        logger.setLevel("INFO")
        ch = logging.StreamHandler(stream_handler)
        ch.setLevel("INFO")
        ch.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(ch)
        push_active_logger(logger)
        log_buffer = LogfileBuffer(get_active_logger())
        for i in range(0, 100):
            log_buffer.write(
                name + "_" + str(i) + "\n"
            )  # print, logger.info() should all end with a newline
        time.sleep(0.1)

    def get_logs(self):
        return self.as_list(self.captured_output.getvalue())

    @staticmethod
    def as_list(logs):
        logs = logs.strip()
        return logs.split("\n")
