import argparse
import logging
import sys
from typing import Optional, List
from .server import run_server
from . import __version__

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

def main(argv: Optional[List[str]] = None):
    """
    Entry point for the Git Smart HTTP server CLI.
    Parses command line arguments and initializes the server with appropriate logging.

    :param argv: List of command line arguments. Defaults to sys.argv[1:].
    :type argv: Optional[List[str]]
    """
    parser = argparse.ArgumentParser(description="Git Smart HTTP Server")
    parser.add_argument("repo_dir", nargs="?", default="repos", help="Directory to store repositories (default: repos)")
    parser.add_argument("-H", "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("-p", "--port", type=int, default=3000, help="Port to bind to (default: 3000)")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity (can be used multiple times)")
    parser.add_argument("-l", "--logfile", help="Enable logging to file (file log level is always fixed at INFO)")
    parser.add_argument("-t", "--trusted-host", action="append", help="Add a trusted host (can be used multiple times)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    setup_logging(args.verbose, args.logfile)

    trusted_hosts = ["127.0.0.1", "localhost"]
    if args.trusted_host:
        trusted_hosts.extend(args.trusted_host)

    run_server(args.host, args.port, args.repo_dir, trusted_hosts)
