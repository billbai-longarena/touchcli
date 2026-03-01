# TouchCLI Performance SLA Benchmark Plan

## Purpose

Define a repeatable probe plan for signal `S-005`:

- turn target SLA into measurable checks
- provide a local baseline method before Phase 3 frontend integration
- provide a pass/fail gate for CI and release readiness

## SLA Targets

The following targets are consolidated from existing project decisions and protocol docs.

| Dimension | Target | SLO Window |
|-----------|--------|------------|
| Agent response latency (text) | `< 500ms` | p95 |
| WebSocket message round-trip | `< 100ms` | p99 |
| DB query latency | `< 50ms` | p99 |
| Concurrent active users | `>= 1000` | steady-state |
| Service availability | `>= 99.5%` | monthly |

## Probe Scope (Phase 2/3 Boundary)

Current scope is backend-only baseline:

- Go Gateway health endpoint latency
- Python Agent Service health endpoint latency
- API endpoint latency under light and medium load

Out of scope for this step:

- true end-to-end frontend RTT
- production-grade distributed load testing
- long-duration soak test (24h+)

## Probe Script

Use script:

`scripts/s005-latency-probe.sh`

For threshold gate checks, use:

`scripts/s005-latency-gate.sh`

For WebSocket RTT baseline checks, use:

`scripts/s005-websocket-probe.sh`

Default endpoints:

- `http://localhost:8080/health` (gateway)
- `http://localhost:8000/health` (agent-service)

Sample count defaults to `40` requests per endpoint.

### Quick Start

```bash
# Ensure backend services are running
docker compose -f backend/docker-compose.yml up -d

# Run probe with defaults
./scripts/s005-latency-probe.sh

# Run with custom sample size
SAMPLES=80 ./scripts/s005-latency-probe.sh

# Run gate with default thresholds (p95<=300ms, p99<=500ms, 0% failures)
./scripts/s005-latency-gate.sh

# Run stricter gate for pre-release
MAX_P95_MS=150 MAX_P99_MS=300 MAX_FAILURE_RATE=0 ./scripts/s005-latency-gate.sh

# Run WebSocket ping/pong RTT probe
SAMPLES=50 WS_URL=ws://localhost:8080/ws ./scripts/s005-websocket-probe.sh

# Run gate with WebSocket enforcement enabled
ENABLE_WS_GATE=1 WS_MAX_P99_MS=100 WS_SAMPLES=20 WS_URL=ws://localhost:8080/ws ./scripts/s005-latency-gate.sh
```

## How to Read Output

Script prints per-endpoint metrics:

- `success`: successful HTTP requests
- `failure`: failed requests
- `p50_ms`, `p95_ms`, `p99_ms`: latency percentiles in milliseconds
- `avg_ms`: average latency in milliseconds

Suggested gate:

- Local dev gate: `p95_ms < 300`
- Pre-release gate: `p95_ms < 150`, `p99_ms < 300`, failure rate `= 0%`
- WebSocket target: `p99_ms < 100`

## Next Step for S-005

1. Add WebSocket RTT probe (message echo/heartbeat delta).
2. Add DB benchmark query set (`customers`, `opportunities`, `messages`) and p99 tracking.
3. Add CI job for probe trend report and threshold check.
