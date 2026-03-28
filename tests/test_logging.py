import logging
import os
import unittest
from git_smart_http.cli import setup_logging

class TestLogging(unittest.TestCase):
    def setUp(self):
        # Clear root logger handlers before each test
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

    def test_console_logging_levels(self):
        # Test default (verbose=0) -> ERROR
        setup_logging(0)
        root = logging.getLogger()
        self.assertEqual(len(root.handlers), 1)
        self.assertIsInstance(root.handlers[0], logging.StreamHandler)
        self.assertEqual(root.handlers[0].level, logging.ERROR)

        # Test verbose=1 -> WARNING
        setup_logging(1)
        root = logging.getLogger()
        self.assertEqual(root.handlers[0].level, logging.WARNING)

        # Test verbose=2 -> INFO
        setup_logging(2)
        root = logging.getLogger()
        self.assertEqual(root.handlers[0].level, logging.INFO)

        # Test verbose=3 -> DEBUG
        setup_logging(3)
        root = logging.getLogger()
        self.assertEqual(root.handlers[0].level, logging.DEBUG)

    def test_file_logging(self):
        logfile = "test_log.log"
        if os.path.exists(logfile):
            os.remove(logfile)
            
        try:
            # Test with logfile and verbose=0
            # Console should be ERROR, File should be INFO
            setup_logging(0, logfile)
            root = logging.getLogger()
            self.assertEqual(len(root.handlers), 2)
            
            # Find handlers
            console_handler = next(h for h in root.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler))
            file_handler = next(h for h in root.handlers if isinstance(h, logging.FileHandler))
            
            self.assertEqual(console_handler.level, logging.ERROR)
            self.assertEqual(file_handler.level, logging.INFO)
            
            # Verify root level is the minimum (INFO in this case because ERROR > INFO)
            self.assertEqual(root.level, logging.INFO)
            
            # Test with logfile and verbose=3
            # Console should be DEBUG, File should be INFO
            setup_logging(3, logfile)
            root = logging.getLogger()
            console_handler = next(h for h in root.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler))
            file_handler = next(h for h in root.handlers if isinstance(h, logging.FileHandler))
            
            self.assertEqual(console_handler.level, logging.DEBUG)
            self.assertEqual(file_handler.level, logging.INFO)
            
            # Verify root level is the minimum (DEBUG in this case because DEBUG < INFO)
            self.assertEqual(root.level, logging.DEBUG)
            
        finally:
            # Cleanup
            root = logging.getLogger()
            for handler in root.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                root.removeHandler(handler)
            if os.path.exists(logfile):
                os.remove(logfile)

if __name__ == "__main__":
    unittest.main()
