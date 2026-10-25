#!/usr/bin/env python3
"""Install/restore FEX with a complete original backup and rollback on copy errors."""
import argparse
import fcntl
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

FILES = tuple("usr/bin/" + name for name in (
    "FEX", "FEXBash", "FEXGetConfig", "FEXOfflineCompiler", "FEXServer", "FEXServerManager", "FEXpidof",
)) + ("FEXCompatTool", "VERSIONS.txt", "ConfigTemplate.json")


def validate(root):
    missing = [rel for rel in FILES if not (root / rel).is_file() or (root / rel).stat().st_size == 0]
    if missing:
        raise RuntimeError(f"Incomplete runtime at {root}: {', '.join(missing)}")


def copy_files(source, target):
    for rel in FILES:
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".hd2-", dir=dest.parent)
        os.close(fd)
        try:
            shutil.copy2(source / rel, temporary)
            os.replace(temporary, dest)
        finally:
            Path(temporary).unlink(missing_ok=True)


def require_idle():
    for name in ("FEXServer", "helldivers2.exe"):
        result = subprocess.run(["pgrep", "-x", name], capture_output=True)
        if result.returncode == 0:
            raise RuntimeError(f"{name} is running. Stop Steam games and wait for FEX to exit, then retry.")
        if result.returncode != 1:
            raise RuntimeError("Could not check for running games; no runtime files changed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", default="install", choices=("install", "restore", "status"))
    args = parser.parse_args()
    state = Path(os.environ.get("STATE_DIR", str(Path.home() / ".local/share/helldivers2-mac-eac-fix")))
    target = Path(os.environ.get("FEX_TOOL_DIR", str(Path.home() / ".local/share/Steam/steamapps/common/FEX-Emu")))
    stage = Path(os.environ.get("STAGE", str(state / "stage")))
    backup = state / "original-fex"
    if args.action == "status":
        print("Original backup:", "present" if backup.is_dir() else "absent")
        print("Built runtime:", "present" if stage.is_dir() else "absent")
        versions = target / "VERSIONS.txt"
        if versions.is_file():
            print(versions.read_text().strip())
        return
    require_idle()
    state.mkdir(parents=True, exist_ok=True)
    with (state / ".install.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another runtime installation is running.") from None
        source = backup if args.action == "restore" else stage
        validate(source)
        validate(target)
        if all((source / rel).read_bytes() == (target / rel).read_bytes() for rel in FILES):
            print("Runtime already matches; no files changed.")
            return
        if args.action == "install" and not backup.exists():
            with tempfile.TemporaryDirectory(prefix=".backup-", dir=state) as temporary:
                snapshot = Path(temporary) / "original"
                copy_files(target, snapshot)
                validate(snapshot)
                os.replace(snapshot, backup)
        if backup.exists():
            validate(backup)
        with tempfile.TemporaryDirectory(prefix=".rollback-", dir=state) as temporary:
            previous = Path(temporary)
            copy_files(target, previous)
            try:
                copy_files(source, target)
                if not all((source / rel).read_bytes() == (target / rel).read_bytes() for rel in FILES):
                    raise RuntimeError("Runtime verification failed.")
            except BaseException:
                copy_files(previous, target)
                raise
        print("Original FEX restored." if args.action == "restore" else "HD2 FEX runtime installed. Original files backed up.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError) as exc:
        raise SystemExit(str(exc))
