import subprocess
from typing import Protocol, List, Optional, NamedTuple

class CommandResult(NamedTuple):
    """
    Holds the result of a process invocation.
    
    returncode
        The exit code if the process terminated within the timeout.
    timed_out
        True if the process is still running after the timeout.
    """
    returncode: Optional[int]
    timed_out: bool

class ProcessInvoker(Protocol):
    """
    Protocol for invoking a command with a timeout.
    """

    def invoke(self, command: List[str], timeout: float) -> CommandResult:
        """
        Invoke the given command, waiting up to timeout seconds.

        Parameters
        ----------
        command : list[str]
            The command and its arguments to execute.
        timeout : float
            Maximum time to wait for command to complete.

        Returns
        -------
        CommandResult
            The result of the invocation.
        """
        ...

class SubprocessInvoker:
    """
    Default implementation of ProcessInvoker that uses subprocess.Popen.
    """

    def invoke(self, command: List[str], timeout: float) -> CommandResult:
        """
        Invoke the given command using subprocess.Popen.

        Parameters
        ----------
        command : list[str]
            The command and its arguments to execute.
        timeout : float
            Maximum time to wait for command to complete.

        Returns
        -------
        CommandResult
            The exit code and whether the process timed out.
        """
        proc = subprocess.Popen(command)
        try:
            proc.wait(timeout=timeout)
            return CommandResult(proc.returncode, False)
        except subprocess.TimeoutExpired:
            # Still running => timed out
            return CommandResult(None, True)
