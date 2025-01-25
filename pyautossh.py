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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--autossh-max-connection-attempts",
        dest="max_connection_attempts",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--autossh-reconnect-delay", dest="reconnect_delay", type=float, default=1.0
    )
    parser.add_argument("--autossh-verbose", dest="verbose", action="store_true")
    return parser.parse_known_args(argv)


def setup_logging(verbose: bool = False) -> None:
    level = logging.INFO if not verbose else logging.DEBUG
    logging.basicConfig(
        level=level, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )


def connect_ssh(
    ssh_args: list[str],
    max_connection_attempts: int | None = 10,
    reconnect_delay: float = 1.0,
) -> None:
    ssh_exec = shutil.which("ssh")
    if ssh_exec:
        logger.debug(f"ssh executable: {ssh_exec}")
    else:
        raise SSHClientNotFound("SSH client executable not found")

    num_attempt = 0
    while max_connection_attempts is None or num_attempt < max_connection_attempts:
        num_attempt += 1

        with subprocess.Popen([ssh_exec] + ssh_args) as ssh_proc:
            try:
                ssh_proc.wait(timeout=30.0)
            except subprocess.TimeoutExpired:
                # Connection is OK
                num_attempt = 0

        if ssh_proc.returncode == 0:
            return

        logger.debug(f"ssh exited with code {ssh_proc.returncode}")
        time.sleep(reconnect_delay)
        logger.debug("Reconnecting...")

    raise SSHConnectionError("Exceeded maximum number of connection attempts")


if __name__ == "__main__":
    sys.exit(main())
