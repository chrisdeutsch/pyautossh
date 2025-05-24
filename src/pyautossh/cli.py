import argparse
import logging

from pyautossh.exceptions import SSHClientNotFound, SSHConnectionError
from pyautossh.pyautossh import SSHAutoConnector

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    """
    Entry point for the pyautossh application.

    Creates the argument parser, parses command line arguments, sets up logging,
    and attempts to establish an SSH connection with automatic reconnection.

    Parameters
    ----------
    argv: list[str] | None
        Command line arguments. If None, sys.argv[1:] is used.

    Returns
    -------
    int
        Exit code: 0 for success, any non-zero value indicates an error
    """

    parser = create_parser()
    args, ssh_args = parser.parse_known_args(argv)
    setup_logging(verbose=args.verbose)

    if not ssh_args:
        parser.print_help()
        return 255

    try:
        connector = SSHAutoConnector()
        connector.connect(
            ssh_args=ssh_args,
            max_connection_attempts=args.max_connection_attempts,
            reconnect_delay=args.reconnect_delay,
        )
    except (SSHClientNotFound, SSHConnectionError) as exce:
        logger.error(str(exce))
        return 255
    except KeyboardInterrupt:
        return 255
    except BaseException:
        logger.exception("Encountered unhandled exception")
        return 255

    return 0


def create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for pyautossh.

    Returns
    -------
    argparse.ArgumentParser
        The configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Automatically reconnect SSH sessions when they disconnect"
    )
    parser.add_argument(
        "--autossh-max-connection-attempts",
        dest="max_connection_attempts",
        type=int,
        default=None,
        help="Maximum number of connection attempts before giving up (default: unlimited)",
    )
    parser.add_argument(
        "--autossh-reconnect-delay",
        dest="reconnect_delay",
        type=float,
        default=1.0,
        help="Delay in seconds between reconnection attempts (default: 1.0)",
    )
    parser.add_argument(
        "--autossh-verbose",
        dest="verbose",
        action="store_true",
        help="Enable verbose logging output",
    )
    return parser


def setup_logging(verbose: bool = False) -> None:
    """Sets up application-wide logging configuration."""

    level = logging.INFO if not verbose else logging.DEBUG
    logging.basicConfig(
        level=level, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
