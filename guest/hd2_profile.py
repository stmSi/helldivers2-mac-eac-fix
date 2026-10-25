#!/usr/bin/env python3
"""Keep the HD2 launch profile in FX, independent of Steam accounts and Windows."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from install_fex import require_idle

MARKER = b"HD2_FX_LOCAL_PROFILE_V1"
TOKEN = re.compile(r'//[^\r\n]*|"(?:\\[\s\S]|[^"\\])*"|[{}]|[^\s{}"]+')


def vdf_scalars(text):
    tokens = []
    end = 0
    for match in TOKEN.finditer(text):
        if text[end:match.start()].strip():
            raise ValueError("Invalid Steam VDF syntax; file left unchanged.")
        end = match.end()
        if not match.group().startswith("//"):
            tokens.append(match)
    if text[end:].strip():
        raise ValueError("Invalid Steam VDF syntax; file left unchanged.")
    position = 0
    entries = []

    def value(token):
        raw = token.group()
        return raw[1:-1].replace('\\"', '"').replace('\\\\', '\\') if raw.startswith('"') else raw

    def block(path, nested=False):
        nonlocal position
        while position < len(tokens):
            key = tokens[position]
            position += 1
            if key.group() == "}" and nested:
                return
            if key.group() in ("{", "}") or position == len(tokens):
                raise ValueError("Invalid Steam VDF structure; file left unchanged.")
            item = tokens[position]
            position += 1
            item_path = path + (value(key).casefold(),)
            if item.group() == "{":
                block(item_path, True)
            elif item.group() == "}":
                raise ValueError("Invalid Steam VDF value; file left unchanged.")
            else:
                entries.append((item_path, key.start(), item.end(), value(item)))
        if nested:
            raise ValueError("Unclosed Steam VDF object; file left unchanged.")

    block(())
    return entries


def remove_fx_launch_options(text):
    removals = []
    for path, start, end, value in vdf_scalars(text):
        if path[-3:] == ("apps", "553850", "launchoptions") and any(
            flag in value for flag in ("FEX_NEEDSSECCOMP=", "FEX_DISKCACHE=", "PROTON_EAC_RUNTIME=")
        ):
            begin = text.rfind("\n", 0, start) + 1
            finish = text.find("\n", end)
            finish = len(text) if finish < 0 else finish + 1
            if not text[begin:start].strip() and not text[end:finish].strip():
                start, end = begin, finish
            removals.append((start, end))
    for start, end in reversed(removals):
        text = text[:start] + text[end:]
    return text, len(removals)


def atomic_write(path, data, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".hd2-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def migrate_accounts(steam, state):
    changed = 0
    backups = state / "private-account-backups"
    for path in sorted((steam / "userdata").glob("*/config/localconfig.vdf")):
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        updated, count = remove_fx_launch_options(text)
        if not count:
            continue
        backups.mkdir(mode=0o700, parents=True, exist_ok=True)
        backup = backups / (hashlib.sha256(raw).hexdigest() + ".vdf")
        if not backup.exists():
            atomic_write(backup, raw, 0o600)
        atomic_write(path, updated.encode("utf-8"), path.stat().st_mode & 0o777)
        changed += count
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "restore", "status"), nargs="?", default="install")
    parser.add_argument("--renderer", choices=("dxmt", "vulkan"), default="dxmt")
    args = parser.parse_args()
    steam = Path(os.environ.get("STEAM_ROOT", str(Path.home() / ".local/share/Steam")))
    tool = Path(os.environ.get("FEX_TOOL_DIR", str(steam / "steamapps/common/FEX-Emu")))
    state = Path(os.environ.get("STATE_DIR", str(Path.home() / ".local/share/helldivers2-mac-eac-fix")))
    launcher = tool / "fex-compat-tool"
    original = tool / ".hd2-fx-original-launcher"
    renderer = tool / ".hd2-fx-renderer"
    wrapper = Path(__file__).with_name("hd2-launcher.sh").read_bytes()
    metadata = state / "profile.json"
    current = launcher.read_bytes()
    if args.action == "status":
        print("HD2 FX local profile:", "enabled" if MARKER in current else "absent")
        if renderer.exists():
            print("Local renderer:", renderer.read_text().strip())
        return
    require_idle()
    if subprocess.run(["pgrep", "-x", "steam"], capture_output=True).returncode == 0:
        raise RuntimeError("Stop the Steam client before changing its local profile.")
    state.mkdir(mode=0o700, parents=True, exist_ok=True)
    if MARKER in current:
        saved = json.loads(metadata.read_text())
        if hashlib.sha256(current).hexdigest() != saved["wrapper_sha256"]:
            raise RuntimeError("Local launcher was edited; refusing to overwrite it.")
        if not original.is_file() or hashlib.sha256(original.read_bytes()).hexdigest() != saved["original_sha256"]:
            raise RuntimeError("Original FEX launcher backup is missing or changed.")
    if args.action == "restore":
        if MARKER not in current:
            print("Local HD2 profile is already absent.")
            return
        atomic_write(launcher, original.read_bytes(), original.stat().st_mode & 0o777)
        original.unlink()
        renderer.unlink(missing_ok=True)
        metadata.unlink()
        print("Original FEX launcher restored. Steam launch options remain empty.")
        return
    if MARKER not in current:
        atomic_write(original, current, launcher.stat().st_mode & 0o777)
    saved = {
        "wrapper_sha256": hashlib.sha256(wrapper).hexdigest(),
        "original_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
    }
    atomic_write(metadata, (json.dumps(saved, indent=2) + "\n").encode(), 0o600)
    atomic_write(renderer, (args.renderer + "\n").encode(), 0o644)
    atomic_write(launcher, wrapper, 0o755)
    changed = migrate_accounts(steam, state)
    print(f"HD2 FX local profile installed. Removed {changed} old FX launch-option entries.")
    print("Steam launch options can stay empty, including after switching accounts.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc))
