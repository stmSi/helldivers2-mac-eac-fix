#!/bin/bash
# Optional launcher-only rebuild. The running VM and all GPU libraries are preserved.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
APP=${FX_APP:-'/Applications/FX Steam Launcher.app'}
WORK="$ROOT/.local-state/shortcut"
SOURCE="$WORK/steamac"
HEADERS="$WORK/libkrun"
PREFIX="$WORK/prefix"
CANDIDATE="$WORK/FX Steam Launcher.patched.app"
[[ $(uname -s) == Darwin ]] || { echo 'Run on macOS.' >&2; exit 1; }
[[ ${1:-} == '' || ${1:-} == --install ]] || { echo 'Usage: build-fx-shortcut.sh [--install]' >&2; exit 1; }
if [[ ${1:-} == --install ]] && pgrep -x steamac-vm >/dev/null; then
  echo 'Quit FX before installing this shortcut build.' >&2; exit 1
fi
value() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$ROOT/versions.json" "$1"; }
FX_SHA=$(value fx_commit)
FX_TAG=$(value fx_tag)
PATCH="$ROOT/patches/fx-ctrl-g.patch"
[[ $(shasum -a 256 "$PATCH" | cut -d ' ' -f 1) == "$(value fx_shortcut_patch_sha256)" ]] || { echo 'Shortcut patch checksum mismatch.' >&2; exit 1; }
installed=$(/usr/libexec/PlistBuddy -c 'Print :SteamacGitCommit' "$APP/Contents/Info.plist")
[[ $installed == "${FX_SHA:0:10}"* ]] || { echo 'This shortcut build supports FX 1.9-eac.2 only.' >&2; exit 1; }
mkdir -p "$WORK" "$PREFIX/include" "$PREFIX/lib"
if [[ ! -e $CANDIDATE ]]; then
[[ -d $SOURCE/.git ]] || git clone --depth 1 --branch "$FX_TAG" https://github.com/StonkGuy/steamac.git "$SOURCE"
[[ $(git -C "$SOURCE" rev-parse HEAD) == "$FX_SHA" ]] || { echo 'Unexpected FX source version.' >&2; exit 1; }
if git -C "$SOURCE" diff --quiet HEAD; then
  git -C "$SOURCE" apply --check "$PATCH"
  git -C "$SOURCE" apply "$PATCH"
else
  [[ $(git -C "$SOURCE" diff | shasum -a 256 | cut -d ' ' -f 1) == "$(value fx_shortcut_patch_sha256)" ]] || {
    echo 'Shortcut source contains other edits; use a fresh .local-state/shortcut directory.' >&2; exit 1;
  }
fi
if [[ ! -f $PREFIX/include/libkrun_input.h ]]; then
  [[ -d $HEADERS/.git ]] || git init -q "$HEADERS"
  git -C "$HEADERS" fetch -q --depth 1 https://github.com/libkrun/libkrun.git 227b2de6ed323fe180e02f871c5f325a90c13cc2
  git -C "$HEADERS" checkout -q --detach FETCH_HEAD
  for patch in "$SOURCE"/host/libkrun/patches/*.patch; do
    git -C "$HEADERS" apply --allow-empty --include='*.h' "$patch"
  done
  cp "$HEADERS"/include/libkrun{,_display,_input}.h "$PREFIX/include/"
fi
cp -p "$APP"/Contents/Frameworks/*.dylib "$PREFIX/lib/"
[[ -e $PREFIX/lib/libkrun.dylib ]] || ln -s libkrun.1.dylib "$PREFIX/lib/libkrun.dylib"
LAUNCHER="$SOURCE/host/launcher"
bash "$LAUNCHER/fetch-zstd.sh"
cp "$APP/Contents/Info.plist" "$WORK/Info.plist"
/usr/libexec/PlistBuddy -c "Set :SteamacGitCommit ${FX_SHA:0:10}-local-ctrlg" "$WORK/Info.plist"
swift build -c release -j 2 --package-path "$LAUNCHER" \
  -Xcc "-I$PREFIX/include" -Xlinker "-L$PREFIX/lib" \
  -Xlinker -rpath -Xlinker '@executable_path/../Frameworks' \
  -Xlinker -rpath -Xlinker "$PREFIX/lib" \
  -Xlinker -sectcreate -Xlinker __TEXT -Xlinker __info_plist -Xlinker "$WORK/Info.plist"
[[ -d "$WORK/FX Steam Launcher.original.app" ]] || cp -cR "$APP" "$WORK/FX Steam Launcher.original.app"
cp -cR "$APP" "$CANDIDATE"
cp "$LAUNCHER/.build/release/steamac-vm" "$CANDIDATE/Contents/MacOS/steamac-vm"
cp "$WORK/Info.plist" "$CANDIDATE/Contents/Info.plist"
codesign --force --sign - --entitlements "$LAUNCHER/steamac-vm.entitlements" "$CANDIDATE"
fi
candidate_build=$(/usr/libexec/PlistBuddy -c 'Print :SteamacGitCommit' "$CANDIDATE/Contents/Info.plist")
[[ $candidate_build == "${FX_SHA:0:10}-local-ctrlg" ]] || { echo 'Unexpected candidate app build.' >&2; exit 1; }
codesign --verify --deep --strict "$CANDIDATE"
python3 - "$APP" "$CANDIDATE" <<'PY'
from pathlib import Path
import hashlib,sys
original,candidate=map(Path,sys.argv[1:])
for path in (original/'Contents/Frameworks').glob('*.dylib'):
    other=candidate/'Contents/Frameworks'/path.name
    if hashlib.sha256(path.read_bytes()).digest()!=hashlib.sha256(other.read_bytes()).digest():
        raise SystemExit('Candidate GPU/VM library differs: '+path.name)
PY
"$CANDIDATE/Contents/MacOS/steamac-vm" --no-crash-reports --selftest-game-layers
"$CANDIDATE/Contents/MacOS/steamac-vm" --no-crash-reports --selftest-graphics-path --graphics-path dxmt
if [[ ${1:-} == --install ]]; then
  pgrep -x steamac-vm >/dev/null && { echo 'FX restarted; app installation deferred.' >&2; exit 1; }
  staged="$(dirname "$APP")/.FX Steam Launcher.ctrlg-$(date +%Y%m%d-%H%M%S).app"
  cp -cR "$CANDIDATE" "$staged"
  python3 - "$staged" "$APP" <<'PY'
import ctypes,os,subprocess,sys
if subprocess.run(['pgrep','-x','steamac-vm'],capture_output=True).returncode==0:
    raise SystemExit('FX is running; no app swap performed.')
libc=ctypes.CDLL(None,use_errno=True)
swap=libc.renamex_np
swap.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_uint]
swap.restype=ctypes.c_int
if swap(os.fsencode(sys.argv[1]),os.fsencode(sys.argv[2]),2):
    error=ctypes.get_errno()
    raise OSError(error,os.strerror(error))
print('Control+G installed. Open FX normally. Previous app: '+sys.argv[1])
PY
else
  printf 'Prepared: %s\n' "$CANDIDATE"
fi
