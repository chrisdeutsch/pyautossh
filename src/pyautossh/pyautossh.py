import logging
import shutil
import subprocess
from typing import Callable, Protocol

from pyautossh.exceptions import SSHClientNotFound, SSHConnectionError
from pyautossh.retry_policy import RetryPolicy

logger = logging.getLogger(__name__)


# Default implementation for finding SSH executable
def default_find_ssh_executable() -> str:
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
        logger.debug(f"ssh executable found via PATH: {ssh_exec}")
        return ssh_exec
    raise SSHClientNotFound("SSH client executable not found")


# Default implementation for attempting an SSH connection
def default_attempt_connection(
    ssh_exec: str,
    ssh_args: list[str],
    *,
    process_timeout_seconds: float = 30.0,
) -> bool:
    """
    Attempt an SSH connection using subprocess and determine if it completed successfully.

    Parameters
    ----------
    ssh_exec: str
        Path to the SSH executable
    ssh_args: list[str]
        Arguments forwarded to the SSH command
    process_timeout_seconds: float
        Time to wait for SSH process to terminate; if it doesn't,
        the connection is considered active (not a terminal success).
        Default is 30.0.

    Returns
    -------
    bool
        True if SSH process completed with exit code 0, False if it is still
        running or exited with an error.
    """
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


class ConnectionAttempter(Protocol):
    """
    Protocol for a function that attempts an SSH connection.
    """

    def __call__(
        self,
        ssh_exec: str,
        ssh_args: list[str],
        *,
        process_timeout_seconds: float = 30.0,
    ) -> bool: ...


class SSHSessionManager:
    """
    Manages an SSH connection with automatic reconnection capabilities.
    Relies on injected functions for finding the SSH executable and attempting connections.
    """

    def __init__(
        self,
        ssh_finder: Callable[[], str] = default_find_ssh_executable,
        connection_attempter: ConnectionAttempter = default_attempt_connection,
    ):
        """
        Initializes the SSHSessionManager.

        Parameters
        ----------
        ssh_finder : Callable[[], str], optional
            A function that returns the path to the SSH executable.
            Defaults to `default_find_ssh_executable`.
        connection_attempter : ConnectionAttempter, optional
            A function that attempts an SSH connection.
            It should take `ssh_exec` (str), `ssh_args` (list[str]),
            and a keyword-only `process_timeout_seconds` (float),
            returning True for a successful terminal connection, False otherwise.
            Defaults to `default_attempt_connection`.
        """
        self._find_ssh_executable_func = ssh_finder
        self._attempt_connection_func = connection_attempter

    def _find_ssh_executable(self) -> str:
        """
        Find the SSH executable using the injected finder function.
        """
        return self._find_ssh_executable_func()

    def _attempt_connection(
        self,
        ssh_exec: str,
        ssh_args: list[str],
        *,
        process_timeout_seconds: float = 30.0,
    ) -> bool:
        """
        Attempt an SSH connection using the injected attempter function.
        """
        return self._attempt_connection_func(
            ssh_exec, ssh_args, process_timeout_seconds=process_timeout_seconds
        )

    def connect(
        self,
        ssh_args: list[str],
        max_connection_attempts: int | None = None,
        reconnect_delay: float = 1.0,
    ) -> None:
        """
        Establish and maintain an SSH connection with automatic reconnection.

        Parameters
        ----------
        ssh_args: list[str]
            Arguments to pass to the SSH command
        max_connection_attempts: int | None
            Maximum number of consecutive failed connection attempts before giving up.
            If None, will try indefinitely. Default is None.
        reconnect_delay: float
            Time in seconds to wait between reconnection attempts. Default is 1.0.

        Raises
        ------
        SSHConnectionError
            If the maximum number of connection attempts is reached
        SSHClientNotFound
            If the SSH executable is not found
        """
        ssh_exec = self._find_ssh_executable()

        retry_policy = RetryPolicy(max_attempts=max_connection_attempts, delay=reconnect_delay)
        success = retry_policy.call(lambda: self._attempt_connection(ssh_exec, ssh_args))
        if not success:
            raise SSHConnectionError("Exceeded maximum number of connection attempts")
