import argparse
import logging
import sys
from typing import Optional, List
from .server import run_server
from .cli import setup_logging

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

    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    setup_logging(args.verbose, args.logfile)

    trusted_hosts = ["127.0.0.1", "localhost"]
    if args.trusted_host:
        trusted_hosts.extend(args.trusted_host)

    run_server(args.host, args.port, args.repo_dir, trusted_hosts)

if __name__ == "__main__":
    main()
