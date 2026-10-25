"""Local FX guest access. Credentials stay in memory; no Steam account files are read."""
import os
from pathlib import Path
import shlex
import subprocess
import sys

import paramiko

ROOT = Path(__file__).resolve().parents[1]


class Guest:
    def __init__(self):
        app = Path(os.environ.get("FX_APP", "/Applications/FX Steam Launcher.app"))
        disk = Path(os.environ.get("FX_DISK", str(Path.home() / "Library/Application Support/es.fxgam.steamac/steamos.img")))
        result = subprocess.run(
            [str(app / "Contents/MacOS/steamac-vm"), "--no-crash-reports", "--ssh-password", str(disk)],
            capture_output=True, text=True, timeout=90, check=False,
        )
        fields = dict(line.split(" ", 1) for line in result.stdout.splitlines() if " " in line)
        if result.returncode or not fields.get("password"):
            raise RuntimeError("Boot FX with SSH enabled before running this installer.")
        self._password = fields["password"]
        state = ROOT / ".local-state"
        state.mkdir(mode=0o700, exist_ok=True)
        self._known_hosts = state / "known_hosts"
        self.client = paramiko.SSHClient()
        if self._known_hosts.exists():
            self.client.load_host_keys(str(self._known_hosts))
        # First trust is restricted to the user's FX instance on localhost.
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(
                "127.0.0.1", port=int(os.environ.get("FX_SSH_PORT", "2222")),
                username=fields.get("user", "steamos"), password=self._password,
                allow_agent=False, look_for_keys=False, timeout=15, auth_timeout=15,
            )
        except paramiko.ssh_exception.NoValidConnectionsError:
            self.client.close()
            self._password = None
            raise RuntimeError("Start the FX VM with SSH enabled on the configured port, then retry.") from None
        self.client.save_host_keys(str(self._known_hosts))

    def run(self, args, capture=False, sudo=False, check=True):
        transport = self.client.get_transport()
        if transport is None:
            raise RuntimeError("The guest SSH connection closed.")
        command = shlex.join([str(arg) for arg in args])
        if sudo:
            command = "sudo -S -p '' " + command
        chunks = []
        with transport.open_session(timeout=15) as channel:
            channel.set_combine_stderr(True)
            channel.exec_command(command)
            if sudo:
                channel.sendall((self._password + "\n").encode())
            channel.shutdown_write()
            while True:
                data = channel.recv(65536)
                if not data:
                    break
                if capture:
                    chunks.append(data)
                else:
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
            status = channel.recv_exit_status()
        if check and status:
            raise RuntimeError(f"Guest command failed (exit {status}); see the message above.")
        return (status, b"".join(chunks).decode(errors="replace")) if capture else status

    def upload(self, local, remote):
        with self.client.open_sftp() as sftp:
            sftp.put(str(local), str(remote))

    def close(self):
        self.client.close()
        self._password = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
