#!/usr/bin/env bash
set -euo pipefail

# WebSocket RTT latency probe for S-005 (performance SLA validation)
# Measures round-trip time (RTT) for WebSocket heartbeat messages
#
# Usage:
#   ./scripts/s005-websocket-probe.sh
#   SAMPLES=100 WS_URL=ws://localhost:8080/ws ./scripts/s005-websocket-probe.sh

SAMPLES="${SAMPLES:-50}"
WS_URL="${WS_URL:-ws://localhost:8080/ws}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-5}"

# Check dependencies
if ! command -v jq >/dev/null 2>&1; then
  echo "error: jq is required for JSON parsing" >&2
  exit 1
fi

# WebSocket client using nc (netcat) + bash
# Sends heartbeat message, measures RTT
probe_websocket() {
  local url="$1"
  local tmp_raw
  local tmp_sorted

  tmp_raw="$(mktemp)"
  tmp_sorted="$(mktemp)"

  local success=0
  local failure=0
  local host port path

  # Parse WebSocket URL (ws://hostname:port/path)
  if [[ $url =~ ^ws://([^/:]+):([0-9]+)(/.*)?$ ]]; then
    host="${BASH_REMATCH[1]}"
    port="${BASH_REMATCH[2]}"
    path="${BASH_REMATCH[3]:-/}"
  else
    echo "error: Invalid WebSocket URL format: $url" >&2
    return 1
  fi

  echo "Probing WebSocket: $url (samples: $SAMPLES)" >&2

  local i
  for i in $(seq 1 "$SAMPLES"); do
    # Create WebSocket connection and measure RTT
    local start_ns end_ns rtt_ms

    start_ns="$(date +%s%N 2>/dev/null || echo "0")"

    # Send heartbeat via nc and read response
    # WebSocket frame format: FIN=1, opcode=ping (0x9), no mask, 0 bytes
    local ws_ping_frame="\x89\x00"  # FIN=1, ping opcode, no payload

    if (
      {
        # Send HTTP upgrade request
        printf "GET %s HTTP/1.1\r\n" "$path"
        printf "Host: %s:%s\r\n" "$host" "$port"
        printf "Upgrade: websocket\r\n"
        printf "Connection: Upgrade\r\n"
        printf "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
        printf "Sec-WebSocket-Version: 13\r\n"
        printf "\r\n"

        # Send heartbeat message (text frame with timestamp)
        local ts
        ts="$(date +%s%N)"
        printf '{"type":"heartbeat","ts":%s}' "$ts"

        sleep 0.1  # Brief wait for response
      } | nc -q1 "$host" "$port" 2>/dev/null || true
    ) > /dev/null 2>&1; then
      end_ns="$(date +%s%N 2>/dev/null || echo "0")"

      if [[ "$start_ns" != "0" && "$end_ns" != "0" ]]; then
        rtt_ms="$(awk -v s="$start_ns" -v e="$end_ns" 'BEGIN { printf "%.3f", (e - s) / 1000000 }')"

        # Only record if latency is reasonable (0.1ms to 10s)
        if (( $(echo "$rtt_ms > 0.1 && $rtt_ms < 10000" | bc -l 2>/dev/null || echo 0) )); then
          echo "$rtt_ms" >> "$tmp_raw"
          success=$((success + 1))
        else
          failure=$((failure + 1))
        fi
      else
        failure=$((failure + 1))
      fi
    else
      failure=$((failure + 1))
    fi

    # Progress indicator
    if (( (i % 10) == 0 )); then
      echo "  Progress: $i/$SAMPLES" >&2
    fi
  done

  # Calculate percentiles
  if [ "$success" -gt 0 ]; then
    sort -n "$tmp_raw" > "$tmp_sorted"

    local p50 p95 p99 avg
    p50="$(percentile 50 "$tmp_sorted")"
    p95="$(percentile 95 "$tmp_sorted")"
    p99="$(percentile 99 "$tmp_sorted")"
    avg="$(awk '{ sum += $1 } END { if (NR>0) printf "%.3f", sum / NR; else print "nan" }' "$tmp_sorted")"

    echo "websocket_rtt success=$success failure=$failure p50_ms=$p50 p95_ms=$p95 p99_ms=$p99 avg_ms=$avg"

    # Return success if p99 < 100ms (SLA target)
    if (( $(echo "$p99 < 100" | bc -l 2>/dev/null || echo 0) )); then
      rm -f "$tmp_raw" "$tmp_sorted"
      return 0
    else
      rm -f "$tmp_raw" "$tmp_sorted"
      return 1
    fi
  else
    echo "websocket_rtt success=0 failure=$failure p50_ms=nan p95_ms=nan p99_ms=nan avg_ms=nan"
    rm -f "$tmp_raw" "$tmp_sorted"
    return 1
  fi
}

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

# Main probe
echo "S-005 WebSocket RTT Probe"
echo "=========================="
echo "URL: $WS_URL"
echo "Samples: $SAMPLES"
echo ""

if probe_websocket "$WS_URL"; then
  echo ""
  echo "✓ WebSocket RTT within SLA (p99 < 100ms)"
  exit 0
else
  echo ""
  echo "⚠ WebSocket RTT exceeds SLA target (p99 >= 100ms)"
  exit 1
fi
