#!/usr/bin/env bash
# Run the SpecBridge service inside WSL (Ubuntu) on a Windows laptop.
# Why: Windows Smart App Control blocks compiled files LangGraph needs (uuid_utils, xxhash, ormsgpack);
# Linux has no such block. The code and data stay in the Windows project folder; only the venv is in Linux.
#
# Needs WSL mirrored networking (%USERPROFILE%\.wslconfig: [wsl2] networkingMode=mirrored), so that
#   - WSL reaches Ollama on Windows at 127.0.0.1:11434, and
#   - cloudflared on Windows reaches this service at localhost:8765.
#
# Usage (from Windows):
#   wsl -d Ubuntu-24.04 -u root -- bash scripts/wsl_serve.sh setup      # once: Python venv + packages
#   wsl -d Ubuntu-24.04 -u root -- bash scripts/wsl_serve.sh start [serve.py options, e.g. --dry-run]
set -euo pipefail

PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${SPECBRIDGE_VENV:-$HOME/specbridge-venv}"     # in the Linux file system: fast, and no clash with .venv

case "${1:-}" in
  setup)
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq python3.12-venv ca-certificates >/dev/null
    [ -x "$VENV/bin/python" ] || python3.12 -m venv "$VENV"
    "$VENV/bin/python" -m pip install -q --upgrade pip
    "$VENV/bin/python" -m pip install -q -r "$PROJECT/requirements.txt"
    "$VENV/bin/python" -c "import langgraph.checkpoint.sqlite, uuid_utils, xxhash, ormsgpack; print('agent packages load')"
    ;;
  start)
    shift
    cd "$PROJECT"
    # .env holds the Windows path; a real environment variable wins for keys already in .env (specbridge/env.py)
    export SPECBRIDGE_WORKDIR="${SPECBRIDGE_WORKDIR_LINUX:-$PROJECT/data}"
    exec "$VENV/bin/python" -u scripts/serve.py "$@"
    ;;
  *)
    echo "usage: bash scripts/wsl_serve.sh setup | start [serve.py options]" >&2
    exit 2
    ;;
esac
