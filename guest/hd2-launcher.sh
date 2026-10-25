#!/bin/sh
# HD2_FX_LOCAL_PROFILE_V1: account-independent; this file exists only in FX's Linux VM.
set -eu
TOOL=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
if [ "${SteamAppId:-}" = 553850 ] || [ "${SteamGameId:-}" = 553850 ]; then
  export FEX_NEEDSSECCOMP=1 FEX_DISKCACHE=0
  export PROTON_LOG=0 WINEDEBUG=-all PROTON_USE_XALIA=0
  export PROTON_EAC_RUNTIME="${TOOL%/*}/Proton EasyAntiCheat Runtime"
  case ${1:-} in
    run|waitforexitandrun)
      renderer=dxmt
      if [ -f "$TOOL/.hd2-fx-renderer" ]; then renderer=$(cat "$TOOL/.hd2-fx-renderer"); fi
      game=0
      for arg in "$@"; do
        case $arg in *start_protected_game.exe|*helldivers2.exe) game=1 ;; esac
      done
      if [ "$renderer" = dxmt ] && [ "$game" = 1 ]; then
        dx11=0
        for arg in "$@"; do [ "$arg" != --use-d3d11 ] || dx11=1; done
        [ "$dx11" = 1 ] || set -- "$@" --use-d3d11
      fi
      printf '[HD2 FX] Local Linux profile enabled (%s); Steam launch options may stay empty.\n' "$renderer" >&2
      ;;
  esac
fi
exec "$TOOL/.hd2-fx-original-launcher" "$@"
