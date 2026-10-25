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
    parser.add_argument("action", nargs="?", default="install", choices=("install", "restore", "status", "profile"))
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--renderer", choices=("dxmt", "vulkan"), default="dxmt")
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
        if args.action in ("install", "profile", "restore"):
            for process in ("helldivers2.exe", "FEXServer"):
                status = guest.run(["pgrep", "-x", process], capture=True, check=False)[0]
                if status == 0:
                    raise RuntimeError("Stop FX games and wait for FEX to exit, then run this installer again.")
                if status != 1:
                    raise RuntimeError("Could not check for running games; no changes made.")
        guest.run(["mkdir", "-p", remote + "/guest", remote + "/patches"])
        for rel in ("guest/build-fex.sh", "guest/install_fex.py", "guest/dependencies.sh", "guest/hd2_profile.py", "guest/hd2-launcher.sh", "patches/fex-hd2.patch", "versions.json"):
            guest.upload(ROOT / rel, remote + "/" + rel)
        if args.action == "install":
            check = 'for c in clang clang++ cmake ninja ld.lld git python3; do command -v "$c" >/dev/null || exit 1; done'
            missing = guest.run(["sh", "-c", check], capture=True, check=False)[0]
            if missing:
                print("Installing SteamOS compiler dependencies (no system upgrade).", flush=True)
                guest.run(["sh", remote + "/guest/dependencies.sh"], sudo=True)
            guest.run(["env", f"JOBS={args.jobs}", "sh", remote + "/guest/build-fex.sh"])
            guest.run(["python3", remote + "/guest/install_fex.py", "install"])
        if args.action in ("install", "profile", "restore"):
            active = guest.run(["systemctl", "--user", "is-active", "--quiet", "steam.service"], capture=True, check=False)[0] == 0
            if active:
                guest.run(["systemctl", "--user", "stop", "steam.service"])
            try:
                profile_action = "restore" if args.action == "restore" else "install"
                guest.run(["python3", remote + "/guest/hd2_profile.py", profile_action, "--renderer", args.renderer])
                if args.action == "restore":
                    guest.run(["python3", remote + "/guest/install_fex.py", "restore"])
            finally:
                if active:
                    guest.run(["systemctl", "--user", "start", "steam.service"])
        else:
            guest.run(["python3", remote + "/guest/install_fex.py", "status"])
            guest.run(["python3", remote + "/guest/hd2_profile.py", "status"])
    if args.action in ("install", "profile"):
        print("\nHD2's FX-local profile is ready. Leave Steam Launch Options empty.")
        print("Keep x86 Proton Experimental selected in FX, then launch normally on any account.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, paramiko.SSHException) as exc:
        print(f"Setup stopped: {exc}", file=sys.stderr)
        raise SystemExit(1)
