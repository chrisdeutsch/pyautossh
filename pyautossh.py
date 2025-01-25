import argparse
import subprocess
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    _, ssh_args = parser.parse_known_args(argv)
    raise sys.exit(connect(ssh_args))


def connect(ssh_args: list[str]):
    ssh_cmd = ["ssh"] + ssh_args

    while True:
        ssh_proc = subprocess.run(ssh_cmd)
        if ssh_proc.returncode == 0:
            return


if __name__ == "__main__":
    main()
