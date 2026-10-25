#!/bin/sh
# Reproduce the tested source tree; no game files are modified.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
WORK=${WORK:-$HOME/.cache/helldivers2-mac-eac-fix}
SRC=$WORK/FEX
STAGE=${STAGE:-$HOME/.local/share/helldivers2-mac-eac-fix/stage}
[ "$(uname -s)" = Linux ] && [ "$(uname -m)" = aarch64 ] || {
  echo 'Build inside the ARM64 FX SteamOS guest, not on macOS.' >&2; exit 1;
}
value() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$ROOT/versions.json" "$1"; }
BASE=$(value fex_commit)
TAG=$(value fex_tag)
TREE=$(value fex_patched_tree)
PATCH=$ROOT/patches/fex-hd2.patch
EXPECTED=$(value fex_patch_sha256)
ACTUAL=$(sha256sum "$PATCH" | cut -d ' ' -f 1)
[ "$ACTUAL" = "$EXPECTED" ] || { echo 'FEX patch checksum mismatch.' >&2; exit 1; }
if [ ! -e "$SRC" ]; then
  mkdir -p "$WORK"
  git clone --depth 1 --branch "$TAG" --recurse-submodules --shallow-submodules \
    https://github.com/StonkGuy/FEX.git "$SRC"
fi
git -C "$SRC" diff --quiet HEAD || { echo 'FEX source has local edits; refusing to overwrite them.' >&2; exit 1; }
if [ "$(git -C "$SRC" rev-parse HEAD)" = "$BASE" ]; then
  git -C "$SRC" -c user.name='HD2 local build' -c user.email='build@example.invalid' am "$PATCH"
fi
[ "$(git -C "$SRC" rev-parse 'HEAD^{tree}')" = "$TREE" ] || {
  echo "FEX source differs from the tested tree. Use a fresh WORK directory: $WORK" >&2; exit 1;
}
git -C "$SRC" submodule update --init --recursive --depth 1
cmake -S "$SRC" -B "$SRC/build-steam" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
  -DBUILD_STEAM_SUPPORT=ON -DBUILD_TESTING=OFF -DBUILD_THUNKS=OFF \
  -DBUILD_FEXCONFIG=OFF -DENABLE_LTO=OFF -DENABLE_ASSERTIONS=OFF \
  -DTUNE_CPU=native -DCMAKE_CXX_SCAN_FOR_MODULES=OFF -DCMAKE_INSTALL_PREFIX=/usr
cmake --build "$SRC/build-steam" -j"${JOBS:-4}"
DESTDIR="$STAGE" cmake --install "$SRC/build-steam" --component Runtime
echo "Built the tested FEX source tree: $TREE"
