#!/usr/bin/env bash
set -euo pipefail

# Gate script for S-005.
# Runs latency probe and enforces thresholds.
#
# Env vars:
#   MAX_P95_MS        default 300
#   MAX_P99_MS        default 500
#   MAX_FAILURE_RATE  default 0 (percent, integer)
#   SAMPLES           forwarded to probe script
#   TIMEOUT_SECONDS   forwarded to probe script
#   ENDPOINTS         forwarded to probe script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PROBE_SCRIPT="${SCRIPT_DIR}/s005-latency-probe.sh"

MAX_P95_MS="${MAX_P95_MS:-300}"
MAX_P99_MS="${MAX_P99_MS:-500}"
MAX_FAILURE_RATE="${MAX_FAILURE_RATE:-0}"

if [ ! -x "$PROBE_SCRIPT" ]; then
  echo "error: probe script not executable: $PROBE_SCRIPT" >&2
  exit 1
fi

if ! [[ "$MAX_P95_MS" =~ ^[0-9]+$ && "$MAX_P99_MS" =~ ^[0-9]+$ && "$MAX_FAILURE_RATE" =~ ^[0-9]+$ ]]; then
  echo "error: thresholds must be non-negative integers" >&2
  exit 1
fi

output="$("$PROBE_SCRIPT" || true)"
echo "$output"

gate_fail=0

while IFS= read -r line; do
  [ -z "$line" ] && continue

  endpoint="$(echo "$line" | awk '{for(i=1;i<=NF;i++) if($i ~ /^endpoint=/){sub(/^endpoint=/,"",$i); print $i}}')"
  success="$(echo "$line" | awk '{for(i=1;i<=NF;i++) if($i ~ /^success=/){sub(/^success=/,"",$i); print $i}}')"
  failure="$(echo "$line" | awk '{for(i=1;i<=NF;i++) if($i ~ /^failure=/){sub(/^failure=/,"",$i); print $i}}')"
  p95="$(echo "$line" | awk '{for(i=1;i<=NF;i++) if($i ~ /^p95_ms=/){sub(/^p95_ms=/,"",$i); print $i}}')"
  p99="$(echo "$line" | awk '{for(i=1;i<=NF;i++) if($i ~ /^p99_ms=/){sub(/^p99_ms=/,"",$i); print $i}}')"

  if [ -z "$success" ] || [ -z "$failure" ] || [ -z "$p95" ] || [ -z "$p99" ]; then
    echo "gate_fail endpoint=${endpoint:-unknown} reason=parse_error" >&2
    gate_fail=1
    continue
  fi

  total=$((success + failure))
  if [ "$total" -le 0 ]; then
    echo "gate_fail endpoint=${endpoint:-unknown} reason=no_samples" >&2
    gate_fail=1
    continue
  fi

  failure_rate=$((failure * 100 / total))

  awk -v v="$p95" -v max="$MAX_P95_MS" 'BEGIN { exit !(v <= max) }' || {
    echo "gate_fail endpoint=$endpoint metric=p95_ms value=$p95 threshold=$MAX_P95_MS" >&2
    gate_fail=1
  }

  awk -v v="$p99" -v max="$MAX_P99_MS" 'BEGIN { exit !(v <= max) }' || {
    echo "gate_fail endpoint=$endpoint metric=p99_ms value=$p99 threshold=$MAX_P99_MS" >&2
    gate_fail=1
  }

  if [ "$failure_rate" -gt "$MAX_FAILURE_RATE" ]; then
    echo "gate_fail endpoint=$endpoint metric=failure_rate value=${failure_rate}% threshold=${MAX_FAILURE_RATE}%" >&2
    gate_fail=1
  fi
done <<< "$output"

if [ "$gate_fail" -ne 0 ]; then
  echo "S-005 gate: FAIL" >&2
  exit 1
fi

echo "S-005 gate: PASS"
