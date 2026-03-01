#!/usr/bin/env bash
set -euo pipefail

# Simple HTTP latency probe for S-005 baseline measurements.
# Usage:
#   ./scripts/s005-latency-probe.sh
#   SAMPLES=80 ./scripts/s005-latency-probe.sh
#   ENDPOINTS="http://localhost:8080/health http://localhost:8000/health" ./scripts/s005-latency-probe.sh

SAMPLES="${SAMPLES:-40}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-3}"
ENDPOINTS="${ENDPOINTS:-http://localhost:8080/health http://localhost:8000/health}"

if ! command -v curl >/dev/null 2>&1; then
  echo "error: curl is required" >&2
  exit 1
fi

if ! [[ "$SAMPLES" =~ ^[0-9]+$ ]] || [ "$SAMPLES" -le 0 ]; then
  echo "error: SAMPLES must be a positive integer (got: $SAMPLES)" >&2
  exit 1
fi

percentile() {
  local p="$1"
  local file="$2"
  awk -v p="$p" '
    { a[NR] = $1 }
    END {
      if (NR == 0) { print "nan"; exit }
      idx = int((p / 100.0) * NR + 0.999999)
      if (idx < 1) idx = 1
      if (idx > NR) idx = NR
      print a[idx]
    }
  ' "$file"
}

probe_endpoint() {
  local url="$1"
  local tmp_raw
  local tmp_sorted
  tmp_raw="$(mktemp)"
  tmp_sorted="$(mktemp)"
  local success=0
  local failure=0
  local i

  for i in $(seq 1 "$SAMPLES"); do
    # Output is seconds with millisecond precision, e.g. "0.012"
    local t
    t="$(curl -sS -m "$TIMEOUT_SECONDS" -o /dev/null -w '%{time_total}' "$url" 2>/dev/null || true)"
    if [[ "$t" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
      awk -v s="$t" 'BEGIN { printf "%.3f\n", s * 1000 }' >> "$tmp_raw"
      success=$((success + 1))
    else
      failure=$((failure + 1))
    fi
  done

  if [ "$success" -gt 0 ]; then
    sort -n "$tmp_raw" > "$tmp_sorted"
    local p50 p95 p99 avg
    p50="$(percentile 50 "$tmp_sorted")"
    p95="$(percentile 95 "$tmp_sorted")"
    p99="$(percentile 99 "$tmp_sorted")"
    avg="$(awk '{ sum += $1 } END { if (NR>0) printf "%.3f", sum / NR; else print "nan" }' "$tmp_sorted")"
    echo "endpoint=$url success=$success failure=$failure p50_ms=$p50 p95_ms=$p95 p99_ms=$p99 avg_ms=$avg"
  else
    echo "endpoint=$url success=0 failure=$failure p50_ms=nan p95_ms=nan p99_ms=nan avg_ms=nan"
  fi

  rm -f "$tmp_raw" "$tmp_sorted"
}

overall_fail=0
for ep in $ENDPOINTS; do
  probe_endpoint "$ep"
  # Mark non-zero when endpoint is fully unavailable.
  if ! curl -sS -m "$TIMEOUT_SECONDS" -o /dev/null "$ep" 2>/dev/null; then
    overall_fail=1
  fi
done

exit "$overall_fail"
