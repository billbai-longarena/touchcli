#!/usr/bin/env bash
set -euo pipefail

# WebSocket RTT latency probe wrapper for S-005.
# Delegates measurement to Python implementation using protocol ping/pong.
#
# Usage:
#   ./scripts/s005-websocket-probe.sh
#   SAMPLES=100 WS_URL=ws://localhost:8080/ws ./scripts/s005-websocket-probe.sh

SAMPLES="${SAMPLES:-50}"
WS_URL="${WS_URL:-ws://localhost:8080/ws}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-5}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 is required" >&2
  exit 1
fi

PYTHONPATH="${PROJECT_ROOT}/backend/python" \
python3 -m agent_service.s005_websocket_probe \
  --samples="$SAMPLES" \
  --url="$WS_URL" \
  --timeout="$TIMEOUT_SECONDS"
