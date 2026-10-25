#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
[[ $(uname -s) == Darwin ]] || { printf 'Run this command on your Mac.\n' >&2; exit 1; }
if pgrep -x steamac-vm >/dev/null; then
  printf 'Quit FX first, then run this command again. No settings changed.\n' >&2
  exit 1
fi
[[ -d '/Applications/FX Steam Launcher.app' ]] || { printf 'Install FX Steam Launcher in Applications first.\n' >&2; exit 1; }
mkdir -p .local-state
if [[ ! -f .local-state/fx-preferences.before.plist ]]; then
  defaults export es.fxgam.steamac .local-state/fx-preferences.before.plist
fi
ram=$(sysctl -n hw.memsize)
guest_ram=12288
[[ $ram -ge 25769803776 ]] || guest_ram=8192
defaults write es.fxgam.steamac cpus -int 8
defaults write es.fxgam.steamac memMiB -int "$guest_ram"
defaults write es.fxgam.steamac graphicsPath -string dxmt
defaults write es.fxgam.steamac refreshRate -int 120
defaults write es.fxgam.steamac retinaResolution -bool false
defaults write es.fxgam.steamac openFullscreen -bool true
defaults write es.fxgam.steamac sshEnabled -bool true
defaults write es.fxgam.steamac sshPort -int 2222
defaults write es.fxgam.steamac autoCapture.553850 -bool false
printf 'FX configured: DXMT, 120 Hz guest, %s MiB guest RAM, SSH on localhost:2222.\n' "$guest_ram"
printf 'Open FX, keep games stopped, then run ./install.command on your Mac.\n'
