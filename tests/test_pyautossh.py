from typing import Callable, List

import pytest

from pyautossh.exceptions import SSHConnectionError
from pyautossh.pyautossh import SSHSessionManager


# Factory for creating a mock connection attempter
def make_mock_attempt_connection(
    attempt_outcomes: List[bool],
) -> Callable[[str, List[str], float], bool]:
    """
    Creates a mock connection_attempter function.

    Parameters
    ----------
    attempt_outcomes : list[bool]
        A list of boolean values representing the outcomes of successive
        connection attempts. The list will be consumed (items popped)
        by the returned mock function.

    Returns
    -------
    Callable[[str, list[str], float], bool]
        A mock function suitable for use as a connection_attempter.
    """
    # Use a list for `outcomes_mut` to allow modification in the closure
    outcomes_mut = list(attempt_outcomes)

    def mock_attempt_connection_impl(
        ssh_exec: str,
        ssh_args: List[str],
        *,
        process_timeout_seconds: float = 30.0,
    ) -> bool:
        if not outcomes_mut:
            raise IndexError(
                "Not enough pre-defined outcomes for mock_attempt_connection in test setup."
            )
        return outcomes_mut.pop(0)

    return mock_attempt_connection_impl


# Mock SSH finder function
def mock_find_ssh_executable_always_succeeds() -> str:
    """Returns a dummy path for the SSH executable."""
    return "/fake/ssh"


def test_connect_successful_first_attempt():
    """
    Tests that connect succeeds on the first attempt.
    """
    ssh_args_test = ["user@host"]
    attempt_outcomes = [True]

    mock_attempter = make_mock_attempt_connection(attempt_outcomes)
    manager = SSHSessionManager(
        ssh_finder=mock_find_ssh_executable_always_succeeds,
        connection_attempter=mock_attempter,
    )

    manager.connect(ssh_args_test, max_connection_attempts=3, reconnect_delay=0.0)
    # If connect completes without error, and the mock attempter had True as the outcome,
    # it implies one successful call was made.


def test_connect_fail_then_succeed():
    """
    Tests that connect succeeds after a few failed attempts.
    """
    ssh_args_test = ["user@host"]
    attempt_outcomes = [False, False, True]

    mock_attempter = make_mock_attempt_connection(attempt_outcomes)
    manager = SSHSessionManager(
        ssh_finder=mock_find_ssh_executable_always_succeeds,
        connection_attempter=mock_attempter,
    )

    manager.connect(ssh_args_test, max_connection_attempts=5, reconnect_delay=0.0)
    # Successful completion implies the outcomes were consumed as expected.


def test_connect_reaches_attempt_limit():
    """
    Tests that connect raises SSHConnectionError after exceeding max attempts.
    """
    ssh_args_test = ["user@host"]
    max_attempts = 3
    attempt_outcomes = [False] * max_attempts

    mock_attempter = make_mock_attempt_connection(attempt_outcomes)
    manager = SSHSessionManager(
        ssh_finder=mock_find_ssh_executable_always_succeeds,
        connection_attempter=mock_attempter,
    )

    with pytest.raises(
        SSHConnectionError, match="Exceeded maximum number of connection attempts"
    ):
        manager.connect(
            ssh_args_test, max_connection_attempts=max_attempts, reconnect_delay=0.0
        )
