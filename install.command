#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
[[ $(uname -s) == Darwin ]] || { printf 'Run this command on your Mac.\n' >&2; exit 1; }
command -v python3 >/dev/null || { printf 'Install Apple Command Line Tools: xcode-select --install\n' >&2; exit 1; }
python3 -c 'import sys; assert sys.version_info >= (3, 9), "Python 3.9 or newer is required"'
[[ -x .venv/bin/python ]] || python3 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check --quiet -r requirements.txt
exec .venv/bin/python scripts/setup.py "$@"
