import logging
import shutil
from typing import Callable

from pyautossh.exceptions import SSHClientNotFound, SSHConnectionError
from pyautossh.process_invoker import SubprocessInvoker
from pyautossh.retry_policy import RetryPolicy

logger = logging.getLogger(__name__)

SSHArgs = list[str]
ConnectionAttempter = Callable[[str, SSHArgs], bool]


def default_find_ssh_executable() -> str:
    """
    Locate the SSH client on the system PATH.

    Returns
    -------
    str
        Absolute path to the SSH executable.

    Raises
    ------
    SSHClientNotFound
        If the SSH executable cannot be found.
    """
    path = shutil.which("ssh")
    if path:
        logger.debug("SSH executable found: %s", path)
        return path
    raise SSHClientNotFound("SSH client executable not found")


def default_attempt_connection(
    ssh_exec: str,
    ssh_args: SSHArgs,
    process_timeout_seconds: float = 30.0,
) -> bool:
    """
    Try to invoke SSH and return True only if it exits cleanly.

    A still-running process at timeout is treated as an active session
    (not a terminal success), so this returns False in that case.
    """
    invoker = SubprocessInvoker()
    command = [ssh_exec] + ssh_args
    result = invoker.invoke(command, timeout=process_timeout_seconds)

    if result.timed_out:
        return False
    if result.returncode == 0:
        return True

    logger.debug("SSH exited with code %s", result.returncode)
    return False


class SSHSessionManager:
    """
    Manage an SSH session with automatic retry on failure.
    """

    def __init__(
        self,
        ssh_finder: Callable[[], str] = default_find_ssh_executable,
        connection_attempter: ConnectionAttempter = default_attempt_connection,
    ) -> None:
        self._ssh_finder = ssh_finder
        self._conn_attempt = connection_attempter

    def connect(
        self,
        ssh_args: SSHArgs,
        max_connection_attempts: int | None = None,
        reconnect_delay: float = 1.0,
    ) -> None:
        """
        Open an SSH session, retrying on failure up to the given limit.

        Parameters
        ----------
        ssh_args
            Arguments to pass to SSH.
        max_connection_attempts
            Max consecutive failures before giving up (None = infinite).
        reconnect_delay
            Seconds to wait between retries.

        Raises
        ------
        SSHConnectionError
            If the retry limit is reached.
        SSHClientNotFound
            If no SSH executable is found.
        """
        ssh_exec = self._ssh_finder()
        retry = RetryPolicy(max_attempts=max_connection_attempts, delay=reconnect_delay)
        ok = retry.call(lambda: self._conn_attempt(ssh_exec, ssh_args))

        if not ok:
            raise SSHConnectionError("Exceeded maximum number of connection attempts")
