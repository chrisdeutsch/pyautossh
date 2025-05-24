import argparse
import logging
import shutil
import subprocess
import sys
import time

logger = logging.getLogger(__name__)


class SSHClientNotFound(Exception):
    pass


class SSHConnectionError(Exception):
    pass


def main(argv: list[str] | None = None) -> int:
    args, ssh_args = parse_args(argv)
    setup_logging(verbose=args.verbose)

    try:
        connect_ssh(
            ssh_args,
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


def parse_args(argv: list[str] | None = None) -> tuple[argparse.Namespace, list[str]]:
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
    return parser.parse_known_args(argv)


def setup_logging(verbose: bool = False) -> None:
    level = logging.INFO if not verbose else logging.DEBUG
    logging.basicConfig(
        level=level, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )


def _find_ssh_executable() -> str:
    """
    Find the SSH executable on the PATH.

    Returns
    -------
    str
        Path to the SSH executable

    Raises
    ------
    SSHClientNotFound
        If the SSH executable is not found in the PATH
    """

    ssh_exec = shutil.which("ssh")
    if ssh_exec:
        logger.debug(f"ssh executable: {ssh_exec}")
        return ssh_exec

    raise SSHClientNotFound("SSH client executable not found")


def _attempt_connection(ssh_exec: str, ssh_args: list[str]) -> bool:
    """
    Attempt to establish an SSH connection.

    Parameters
    ----------
    ssh_exec : str
        Path to the SSH executable
    ssh_args : list[str]
        Arguments forwarded to the SSH command

    Returns
    -------
    bool
        True if connection was successful and terminated normally,
        False if connection failed or is still active
    """

    # Time to wait for SSH process to terminate; if it doesn't, connection is considered active
    process_timeout_seconds = 30.0
    with subprocess.Popen([ssh_exec] + ssh_args) as ssh_proc:
        try:
            ssh_proc.wait(timeout=process_timeout_seconds)
        except subprocess.TimeoutExpired:
            # Connection is still active. Not a terminal success.
            return False

    if ssh_proc.returncode == 0:
        return True

    logger.debug(f"ssh exited with code {ssh_proc.returncode}")
    return False


def connect_ssh(
    ssh_args: list[str],
    max_connection_attempts: int | None = None,
    reconnect_delay: float = 1.0,
) -> None:
    """
    Establish and maintain an SSH connection with automatic reconnection.

    Parameters
    ----------
    ssh_args : list[str]
        Arguments to pass to the SSH command
    max_connection_attempts : int or None, optional
        Maximum number of consecutive failed connection attempts before giving up.
        If None, will try indefinitely. Default is None (retry indefinitely).
    reconnect_delay : float, optional
        Time in seconds to wait between reconnection attempts. Default is 1.0.

    Raises
    ------
    SSHConnectionError
        If the maximum number of connection attempts is reached
    SSHClientNotFound
        If the SSH executable is not found
    """

    ssh_exec = _find_ssh_executable()

    num_attempt = 0
    while max_connection_attempts is None or num_attempt < max_connection_attempts:
        num_attempt += 1

        if _attempt_connection(ssh_exec, ssh_args):
            return

        logger.debug(f"Waiting {reconnect_delay}s before reconnecting...")
        time.sleep(reconnect_delay)
        logger.debug("Reconnecting...")

    raise SSHConnectionError("Exceeded maximum number of connection attempts")


if __name__ == "__main__":
    sys.exit(main())
