import logging
import shutil
import subprocess
import time

from pyautossh.exceptions import SSHClientNotFound, SSHConnectionError

logger = logging.getLogger(__name__)


class SSHAutoConnector:
    """
    Manages an SSH connection with automatic reconnection capabilities.
    """

    @staticmethod
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

    @staticmethod
    def _attempt_connection(
        ssh_exec: str, ssh_args: list[str], process_timeout_seconds: float = 30.0
    ) -> bool:
        """
        Attempt an SSH connection and determine if it completed successfully.

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

        num_attempt = 0
        while max_connection_attempts is None or num_attempt < max_connection_attempts:
            num_attempt += 1

            if self._attempt_connection(ssh_exec, ssh_args):
                return

            logger.debug(f"Waiting {reconnect_delay}s before reconnecting...")
            time.sleep(reconnect_delay)
            logger.debug("Reconnecting...")

        raise SSHConnectionError("Exceeded maximum number of connection attempts")
