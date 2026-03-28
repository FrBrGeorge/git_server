import logging
import sys
from typing import Optional, List

def setup_logging(verbose_level: int, logfile: Optional[str] = None):
    """
    Configure logging for the application.
    Console logging level is based on the verbosity level.
    File logging level is fixed at INFO if a logfile is provided.

    :param verbose_level: The verbosity level (0-3+).
    :type verbose_level: int
    :param logfile: Path to the log file, if any.
    :type logfile: Optional[str]
    """
    console_level = logging.ERROR
    if verbose_level == 1:
        console_level = logging.WARNING
    elif verbose_level == 2:
        console_level = logging.INFO
    elif verbose_level >= 3:
        console_level = logging.DEBUG

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    # File handler
    if logfile:
        file_handler = logging.FileHandler(logfile)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

    # Root logger configuration
    # Set root logger level to the lowest of the handler levels to ensure messages are captured
    root_level = console_level
    if logfile:
        root_level = min(console_level, logging.INFO)

    # Clear existing handlers if any (useful for testing)
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    logging.basicConfig(
        level=root_level,
        handlers=handlers,
        force=True  # Ensure basicConfig reconfigures even if already called
    )
