#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <config1.json> [config2.json ...]"
  echo "Example: $0 sites/local.json sites/one_line.local.json"
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: $PYTHON_BIN not found. Set PYTHON_BIN or install Python 3." >&2
  exit 1
fi

echo "==> Running local smoke captures"

for cfg in "$@"; do
  if [[ ! -f "$cfg" ]]; then
    echo "ERROR: config not found: $cfg" >&2
    exit 1
  fi
  echo ""
  echo "==> Running smoke capture: $cfg"
  "$PYTHON_BIN" whistleblower.py \
    --config "$cfg" \
    --timeout-ms 120000 \
    --settle-ms 15000 \
    --post-login-wait-ms 15000
done

echo ""
echo "Smoke run complete."
