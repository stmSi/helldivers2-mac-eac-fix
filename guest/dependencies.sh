#!/bin/sh
# Compiler packages for the source build; restores SteamOS's previous read-only state.
set -eu
[ "$(id -u)" = 0 ] || { echo 'Run this dependency step with sudo.' >&2; exit 1; }
command -v pacman >/dev/null || { echo 'This step is for FX SteamOS.' >&2; exit 1; }
restore_ro=0
if command -v steamos-readonly >/dev/null && steamos-readonly status | grep -qi '^enabled$'; then
  steamos-readonly disable
  restore_ro=1
fi
restore() {
  if [ "$restore_ro" = 1 ]; then steamos-readonly enable; fi
}
trap restore EXIT
pacman -S --needed --noconfirm clang cmake ninja lld git python
