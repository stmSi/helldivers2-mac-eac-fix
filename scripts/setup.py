#!/usr/bin/env python3
"""Build/install the HD2 FEX runtime in the user's running FX guest."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import paramiko

from fx_guest import Guest, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", default="install", choices=("install", "restore", "status"))
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    if args.jobs < 1 or args.jobs > 32:
        parser.error("--jobs must be between 1 and 32")
    versions = json.loads((ROOT / "versions.json").read_text())
    patch = ROOT / "patches/fex-hd2.patch"
    if hashlib.sha256(patch.read_bytes()).hexdigest() != versions["fex_patch_sha256"]:
        raise RuntimeError("The FEX patch does not match versions.json.")
    with Guest() as guest:
        _, home = guest.run(["sh", "-c", 'printf %s "$HOME"'], capture=True)
        remote = home + "/.local/share/helldivers2-mac-eac-fix"
        print(f"FX connected. Action: {args.action}", flush=True)
        if args.action == "install":
            status = guest.run(["pgrep", "-x", "helldivers2.exe"], capture=True, check=False)[0]
            if status == 0:
                raise RuntimeError("Stop HD2 in FX Steam first, then run this installer again.")
        guest.run(["mkdir", "-p", remote + "/guest", remote + "/patches"])
        for rel in ("guest/build-fex.sh", "guest/install_fex.py", "guest/dependencies.sh", "patches/fex-hd2.patch", "versions.json"):
            guest.upload(ROOT / rel, remote + "/" + rel)
        if args.action == "install":
            check = 'for c in clang clang++ cmake ninja ld.lld git python3; do command -v "$c" >/dev/null || exit 1; done'
            missing = guest.run(["sh", "-c", check], capture=True, check=False)[0]
            if missing:
                print("Installing SteamOS compiler dependencies (no system upgrade).", flush=True)
                guest.run(["sh", remote + "/guest/dependencies.sh"], sudo=True)
            guest.run(["env", f"JOBS={args.jobs}", "sh", remote + "/guest/build-fex.sh"])
        guest.run(["python3", remote + "/guest/install_fex.py", args.action])
    if args.action == "install":
        print("\nFEX is ready. Paste the README launch options into HD2 in FX Steam.")
        print("Select x86 Proton Experimental, then launch the game normally.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, paramiko.SSHException) as exc:
        print(f"Setup stopped: {exc}", file=sys.stderr)
        raise SystemExit(1)
