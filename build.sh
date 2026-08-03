#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="${PYTHON_BIN_OVERRIDE:-python3}"
fi

if ! "$PYTHON_BIN" -c "import yaml" >/dev/null 2>&1; then
  echo "[knowledge-builder] Missing Python dependencies."
  echo "[knowledge-builder] Run:"
  echo "  python3 -m venv .venv"
  echo "  .venv/bin/pip install -r requirements.txt"
  exit 1
fi

exec "$PYTHON_BIN" -m scripts "$@"
