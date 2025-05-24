import pytest
from pyautossh.pyautossh import SSHSessionManager
from pyautossh.exceptions import SSHConnectionError

# Helper class for testing
class DummySSHSessionManager(SSHSessionManager):
    def __init__(self, attempt_outcomes: list[bool]):
        self.attempt_outcomes_config = list(attempt_outcomes)
        self.find_ssh_executable_call_count = 0
        self.attempt_connection_log = []
        self.fake_ssh_exec_path = "/fake/ssh"

    def _find_ssh_executable(self) -> str:
        self.find_ssh_executable_call_count += 1
        return self.fake_ssh_exec_path

    def _attempt_connection(
        self, ssh_exec: str, ssh_args: list[str], *, process_timeout_seconds: float = 30.0
    ) -> bool:
        self.attempt_connection_log.append(
            {"ssh_exec": ssh_exec, "ssh_args": ssh_args}
        )
        if not self.attempt_outcomes_config:
            raise IndexError(
                "Not enough pre-defined outcomes for _attempt_connection in test setup."
            )
        return self.attempt_outcomes_config.pop(0)


def test_connect_successful_first_attempt():
    """
    Tests that connect succeeds on the first attempt.
    """
    ssh_args_test = ["user@host"]
    # Configure dummy to succeed on the first attempt
    manager = DummySSHSessionManager(attempt_outcomes=[True])

    manager.connect(ssh_args_test, max_connection_attempts=3, reconnect_delay=0.0)

    assert manager.find_ssh_executable_call_count == 1
    assert len(manager.attempt_connection_log) == 1
    assert manager.attempt_connection_log[0]['ssh_exec'] == manager.fake_ssh_exec_path
    assert manager.attempt_connection_log[0]['ssh_args'] == ssh_args_test


def test_connect_fail_then_succeed():
    """
    Tests that connect succeeds after a few failed attempts.
    """
    ssh_args_test = ["user@host"]
    # Configure dummy to fail twice, then succeed
    manager = DummySSHSessionManager(attempt_outcomes=[False, False, True])

    # max_connection_attempts needs to be >= 3 for this test
    manager.connect(ssh_args_test, max_connection_attempts=5, reconnect_delay=0.001)

    assert manager.find_ssh_executable_call_count == 1
    assert len(manager.attempt_connection_log) == 3  # Two failures, one success
    for i in range(3):
        assert manager.attempt_connection_log[i]['ssh_exec'] == manager.fake_ssh_exec_path
        assert manager.attempt_connection_log[i]['ssh_args'] == ssh_args_test


def test_connect_reaches_attempt_limit():
    """
    Tests that connect raises SSHConnectionError after exceeding max attempts.
    """
    ssh_args_test = ["user@host"]
    max_attempts = 3
    # Configure dummy to always fail
    manager = DummySSHSessionManager(attempt_outcomes=[False] * max_attempts)

    with pytest.raises(SSHConnectionError, match="Exceeded maximum number of connection attempts"):
        manager.connect(ssh_args_test, max_connection_attempts=max_attempts, reconnect_delay=0.001)

    assert manager.find_ssh_executable_call_count == 1
    assert len(manager.attempt_connection_log) == max_attempts
    for i in range(max_attempts):
        assert manager.attempt_connection_log[i]['ssh_exec'] == manager.fake_ssh_exec_path
        assert manager.attempt_connection_log[i]['ssh_args'] == ssh_args_test
