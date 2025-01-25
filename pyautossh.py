import argparse
import subprocess
import sys
import time


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reconnect-delay", type=float, default=1.0)
    args, ssh_args = parser.parse_known_args(argv)

    returncode = connect(ssh_args, reconnect_delay=args.reconnect_delay)
    sys.exit(returncode)


def connect(ssh_args: list[str], reconnect_delay: float = 1.0):
    ssh_cmd = ["ssh"] + ssh_args

    while True:
        ssh_proc = subprocess.run(ssh_cmd)
        if ssh_proc.returncode == 0:
            return 0

        time.sleep(reconnect_delay)


if __name__ == "__main__":
    sys.exit(main())
