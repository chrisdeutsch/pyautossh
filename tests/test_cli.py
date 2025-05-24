from pyautossh.cli import parse_args


def test_parse_args_basic():
    """Test basic argument parsing with just a host."""
    args, ssh_args = parse_args(["user@host"])
    assert args.max_connection_attempts is None
    assert args.reconnect_delay == 1.0
    assert args.verbose is False
    assert ssh_args == ["user@host"]


def test_parse_args_with_options():
    """Test parsing with pyautossh-specific options."""
    args, ssh_args = parse_args(
        [
            "--autossh-max-connection-attempts",
            "5",
            "--autossh-reconnect-delay",
            "2.5",
            "user@host",
        ]
    )
    assert args.max_connection_attempts == 5
    assert args.reconnect_delay == 2.5
    assert args.verbose is False
    assert ssh_args == ["user@host"]


def test_parse_args_with_ssh_options():
    """Test parsing with SSH-specific options."""
    args, ssh_args = parse_args(
        ["user@host", "-p", "2222", "-v", "-L", "8080:localhost:8080"]
    )
    assert args.max_connection_attempts is None
    assert args.reconnect_delay == 1.0
    assert args.verbose is False
    assert ssh_args == ["user@host", "-p", "2222", "-v", "-L", "8080:localhost:8080"]


def test_parse_args_mixed_order():
    """Test parsing with mixed order of pyautossh and SSH options."""
    args, ssh_args = parse_args(
        [
            "--autossh-verbose",
            "user@host",
            "--autossh-reconnect-delay",
            "3.0",
            "-p",
            "2222",
        ]
    )
    assert args.verbose is True
    assert args.reconnect_delay == 3.0
    assert args.max_connection_attempts is None
    assert ssh_args == ["user@host", "--autossh-reconnect-delay", "3.0", "-p", "2222"]


def test_parse_args_empty():
    """Test parsing with no arguments."""
    args, ssh_args = parse_args([])
    assert args.max_connection_attempts is None
    assert args.reconnect_delay == 1.0
    assert args.verbose is False
    assert ssh_args == []
