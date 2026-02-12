#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <config1.json> [config2.json ...]"
  echo "Example: $0 sites/local.json sites/one_line.local.json"
  exit 1
fi

echo "==> Building image"
docker build -t whistleblower .

for cfg in "$@"; do
  if [[ ! -f "$cfg" ]]; then
    echo "ERROR: config not found: $cfg" >&2
    exit 1
  fi
  echo ""
  echo "==> Running smoke capture: $cfg"
  docker run --rm \
    -v "$(pwd)/sites:/app/sites" \
    -v "$(pwd)/data:/app/data" \
    whistleblower \
    --config "/app/$cfg" \
    --timeout-ms 120000 \
    --settle-ms 15000 \
    --post-login-wait-ms 15000
done

echo ""
echo "Smoke run complete."
