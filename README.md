# PyAutoSSH

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python tool that automatically reconnects SSH sessions after connection
interruptions. Perfect for maintaining persistent connections when using
terminal multiplexers like `screen` or `tmux` on remote hosts.

## Features

- Automatic reconnection on connection loss
- Compatible with existing SSH configurations
- Minimal dependencies

## Prerequisites

- Python 3.9 or newer
- SSH client (`ssh` command available in PATH)
- Configured SSH key-based authentication (recommended)

## Installation

```bash
# Via pip (or pipx / uvx)
pip install git+https://github.com/chrisdeutsch/pyautossh
pip install pyautossh

# From source
git clone https://github.com/chrisdeutsch/pyautossh
cd pyautossh
pip install .
```

## Usage

### Basic Usage

```bash
pyautossh <args forwarded to ssh>

# For example
pyautossh -t user@hostname tmux new -A -s session_name
```

### Advanced Configuration

Create an SSH config entry in `~/.ssh/config`:

```sshconfig
Host hostname-tmux
    User username
    HostName hostname
    RequestTTY yes
    RemoteCommand tmux new-session -A -s base
    ServerAliveInterval 5
    ServerAliveCountMax 1
```

Then simply connect using:

```bash
pyautossh hostname-tmux
```

The parameters

- `ServerAliveInterval`: Time interval (in seconds) for sending keep-alive
  messages
- `ServerAliveCountMax`: Number of keep-alive messages that can be lost before
  disconnecting
- `RequestTTY`: Forces TTY allocation (required for interactive sessions)

can be configured depending on how aggressively you want to reconnect.

## Tips

1. Always use key-based authentication
2. Configure SSH agent for convenient key management
3. Adjust keep-alive settings based on how aggressive you want to reconnect
4. Use terminal multiplexers for session persistence

## Related Projects

- [autossh](https://github.com/Autossh/autossh) - The original AutoSSH by Carson
  Harding
