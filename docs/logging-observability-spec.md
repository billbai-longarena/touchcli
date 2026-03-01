# TouchCLI Logging & Observability Specification

**Version**: 1.0
**Created**: 2026-03-02
**Phase**: 2 (Task 2.4 prerequisite)
**Purpose**: Define structured logging, error tracking, and distributed tracing standards

---

## Overview

Logging and observability are critical for operating TouchCLI in production. This document defines:

1. **Structured Logging**: JSON format, log levels, sampling
2. **Error Tracking**: Sentry integration, alert rules
3. **Distributed Tracing**: OpenTelemetry hooks
4. **Health Checks**: Endpoint definitions and thresholds

---

## Structured Logging

### Log Format (JSON)

All logs must be JSON objects (one per line) with these mandatory fields:

```json
{
  "timestamp": "2026-03-02T12:00:00.000Z",
  "level": "INFO|WARNING|ERROR|CRITICAL|DEBUG",
  "logger": "module.submodule",
  "message": "Human-readable message",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "span_id": "0e57e58b-0e0f",
  "service": "gateway|agent-service|api-server",
  "version": "1.0.0"
}
```

**Optional contextual fields**:
```json
{
  "user_id": "uuid",
  "conversation_id": "uuid",
  "agent_name": "router|sales|data|strategy|sentinel|memory",
  "action_type": "create_opportunity|execute_query|...",
  "duration_ms": 123,
  "status_code": 200,
  "error_code": "TIMEOUT|DATABASE_ERROR|...",
  "stack_trace": "...",
  "metadata": { "custom_key": "custom_value" }
}
```

### Log Levels

| Level | Severity | Example | Sampling |
|-------|----------|---------|----------|
| **DEBUG** | Low | Function entry/exit, variable values | 5% (sampled) |
| **INFO** | Normal | Request received, operation started | 100% |
| **WARNING** | Medium | Retry attempt, slow query, cache miss | 100% |
| **ERROR** | High | Operation failed, exception caught | 100% |
| **CRITICAL** | Urgent | Service down, data corruption | 100% + Alert |

### Logger Naming

**Go Gateway**:
```
gateway.websocket
gateway.auth
gateway.ratelimit
gateway.health
```

**Python Agent Service**:
```
agent.router
agent.sales
agent.data
agent.strategy
agent.sentinel
agent.memory
agent.tools.sql
agent.tools.crm
```

**Shared**:
```
database.connection
database.query
redis.connection
redis.cache
```

### Sampling Strategy

To prevent log volume explosion:

| Category | Sampling Rate | Exception |
|----------|---------------|-----------|
| DEBUG logs | 5% (in prod) | N/A |
| INFO logs | 100% | 100% on errors |
| WARNING logs | 100% | N/A |
| ERROR logs | 100% | 100% + escalate |
| CRITICAL logs | 100% + Alert | N/A |

**Sampling Decision**:
```python
# Pseudocode
if log_level == "DEBUG":
    if random.random() > 0.05:  # 5% sample
        return  # Skip this log
elif log_level == "INFO":
    if trace_id in error_trace_ids:
        # Always log INFO for error traces
        pass
```

### Structured Logging Examples

**Gateway WebSocket Connection**:
```json
{
  "timestamp": "2026-03-02T12:00:00.000Z",
  "level": "INFO",
  "logger": "gateway.websocket",
  "message": "Client connected",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "service": "gateway",
  "user_id": "user-123",
  "conversation_id": "conv-456",
  "metadata": {
    "client_ip": "192.168.1.1",
    "protocol": "wss",
    "jwt_expires_in": 3600
  }
}
```

**Agent Execution**:
```json
{
  "timestamp": "2026-03-02T12:00:01.500Z",
  "level": "INFO",
  "logger": "agent.router",
  "message": "Router agent executed",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "span_id": "0e57e58b-0e0f",
  "service": "agent-service",
  "agent_name": "router",
  "action_type": "intent_detection",
  "duration_ms": 150,
  "metadata": {
    "intent": "create_opportunity",
    "confidence": 0.92,
    "route_to": "sales"
  }
}
```

**Database Error**:
```json
{
  "timestamp": "2026-03-02T12:00:02.000Z",
  "level": "ERROR",
  "logger": "database.query",
  "message": "SQL query timeout",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "service": "agent-service",
  "error_code": "DATABASE_TIMEOUT",
  "duration_ms": 30000,
  "metadata": {
    "query": "SELECT * FROM customers WHERE ...",
    "db_host": "postgres-primary",
    "timeout_ms": 30000
  },
  "stack_trace": "..."
}
```

---

## Error Tracking (Sentry)

### Sentry Integration

**DSN Configuration**:
```bash
# .env
SENTRY_DSN=https://<key>@<organization>.ingest.sentry.io/<project_id>
SENTRY_ENVIRONMENT=production  # or staging/development
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% for tracing
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 10% for profiling
```

### Error Reporting Rules

| Error Type | Report to Sentry | Alert | Retry |
|------------|------------------|-------|-------|
| Database connection lost | ✅ (ERROR) | 🔴 CRITICAL | Yes (exponential) |
| Query timeout (> 30s) | ✅ (ERROR) | 🟡 WARNING | Yes (3x) |
| Agent execution failed | ✅ (ERROR) | 🔴 if > 3 failures | Yes (2x) |
| Rate limit exceeded | ❌ (INFO only) | No | No (reject) |
| WebSocket disconnection | ✅ (INFO) | No | Client reconnects |
| Invalid JWT token | ❌ (WARNING) | No | Reject request |

### Alert Thresholds

```yaml
alerts:
  error_rate:
    threshold: "> 5% in 5 minutes"  # Error rate spike
    action: "PagerDuty critical alert"

  database_latency:
    threshold: "p99 > 500ms"  # Database slow
    action: "Slack notification"

  agent_timeout:
    threshold: "> 3 timeouts in 10 minutes"
    action: "Auto-restart agent service"

  redis_connection:
    threshold: "connection refused"
    action: "PagerDuty high alert"

  memory_usage:
    threshold: "> 80% of limit"
    action: "Slack warning"
```

### Sentry Issues Grouping

Sentry groups similar errors using:

1. **Exception type** (e.g., `TimeoutError`, `DatabaseError`)
2. **Error message** (first sentence)
3. **Stack trace** (top 3 frames)
4. **URL/Service** (for gateway errors)

Example grouping:
```
Group ID: postgresql-connection-timeout
Occurrences: 145 in last 24h
Last seen: 2 minutes ago
Status: Unresolved
```

---

## Distributed Tracing (OpenTelemetry)

### Trace Propagation

**HTTP Header Propagation** (W3C Trace Context):
```
traceparent: 00-550e8400e29b41d4a716446655440000-0e57e58b0e0f0001-01
tracestate: vendor=value
```

**Trace ID Generation**:
- Generated by Gateway on incoming WebSocket connection
- Propagated to all downstream services (Agent, Database, Redis)
- Included in all logs and error reports

### Span Definition

A **span** represents a single operation within a trace.

```python
# Pseudocode
with tracer.start_as_current_span("router.intent_detection") as span:
    span.set_attribute("input_text", user_message)
    span.set_attribute("intent", detected_intent)
    span.set_attribute("confidence", confidence_score)
    # Do work
    span.set_attribute("output_intent", "create_opportunity")
```

### Key Spans to Instrument

| Service | Span | Attributes |
|---------|------|-----------|
| **Gateway** | websocket.accept | client_id, protocol |
| **Gateway** | http.request | method, path, status_code |
| **Agent** | agent.execute | agent_name, action_type |
| **Agent** | tool.execute | tool_name, tool_version |
| **Database** | db.query.execute | db_system, sql_summary |
| **Redis** | redis.command | operation, key_pattern |

### Trace Visualization Example

```
Trace ID: 550e8400-e29b-41d4-a716-446655440000

websocket.message_received [0ms - 150ms]
  ├─ agent.router [10ms - 160ms]
  │  ├─ tool.intent_detection [20ms - 80ms]
  │  └─ cache.get_context [100ms - 120ms]
  ├─ agent.sales [170ms - 450ms]
  │  ├─ db.query.customers [180ms - 250ms]
  │  ├─ db.query.opportunities [260ms - 350ms]
  │  └─ crm.api.create_opportunity [360ms - 440ms]
  └─ websocket.message_send [460ms - 480ms]

Total trace duration: 480ms
Slowest span: agent.sales (280ms)
Database time: 170ms (35% of total)
```

### Trace Sampling

```yaml
sampling:
  # Always sample error traces
  - rule: "error OR exception"
    sample_rate: 1.0  # 100%

  # Sample slow requests
  - rule: "duration > 1000ms"
    sample_rate: 0.5  # 50%

  # Sample rate-limited requests lightly
  - rule: "status_code == 429"
    sample_rate: 0.1  # 10%

  # Default: light sampling
  - rule: "default"
    sample_rate: 0.1  # 10% of normal requests
```

---

## Health Check Endpoint

### GET /health

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-02T12:00:00Z",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 15,
      "last_checked": "2026-03-02T12:00:00Z"
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 3,
      "last_checked": "2026-03-02T12:00:00Z"
    },
    "agent_service": {
      "status": "healthy",
      "agents_active": 3,
      "last_checked": "2026-03-02T12:00:00Z"
    }
  }
}
```

### Health Check Thresholds

| Component | Healthy | Degraded | Unhealthy |
|-----------|---------|----------|-----------|
| **Database** | latency < 100ms | latency > 500ms | unreachable |
| **Redis** | latency < 10ms | latency > 50ms | unreachable |
| **Agent Service** | active agents > 0 | agents degrading | all failed |
| **Overall** | all healthy | 1+ degraded | 1+ unhealthy |

---

## Metrics Collection

### Key Metrics (using Prometheus)

```
# Request metrics
http_requests_total{service="gateway", method="POST", status="200"}
http_request_duration_seconds{service="gateway", endpoint="/conversations"}

# Database metrics
db_query_duration_seconds{operation="SELECT", table="customers"}
db_connection_pool_size{database="postgres"}

# Agent metrics
agent_execution_duration_seconds{agent="router"}
agent_tool_calls_total{agent="sales", tool="create_opportunity"}

# System metrics
process_resident_memory_bytes{service="gateway"}
go_goroutines{service="gateway"}
```

### Metric Retention

- **High-cardinality metrics** (with many label combinations): 7 days
- **Low-cardinality metrics** (aggregated): 30 days
- **Custom business metrics**: 90 days

---

## Log Aggregation

### Stack

- **Shipper**: Filebeat (Go) / Python logging handler
- **Buffer**: Kafka (optional, for high volume)
- **Storage**: Elasticsearch
- **UI**: Kibana

### Index Naming

```
logs-touchcli-gateway-2026.03.02
logs-touchcli-agent-2026.03.02
logs-touchcli-database-2026.03.02
```

### Retention Policy

- **Logs**: 30 days (hot tier) + 60 days (warm tier)
- **Metrics**: 90 days
- **Traces**: 7 days (sampled)

### Common Kibana Queries

```
# Find all errors in last 1 hour
level: ERROR AND @timestamp > now-1h

# Find slow agent executions
logger: agent.* AND duration_ms > 1000

# Find customer-specific conversation issues
user_id: "user-123" AND level: ERROR

# Agent performance by type
agent_name: * | stats avg(duration_ms) by agent_name
```

---

## Development vs Production Configuration

### Development (`development`)

```yaml
log_level: DEBUG
sentry_enabled: false
traces_sample_rate: 1.0  # 100% sampling
health_check_interval: 10s
```

### Staging (`staging`)

```yaml
log_level: INFO
sentry_enabled: true
traces_sample_rate: 0.5  # 50% sampling
health_check_interval: 30s
```

### Production (`production`)

```yaml
log_level: INFO
sentry_enabled: true
traces_sample_rate: 0.1  # 10% sampling
health_check_interval: 60s
debug_mode: false
```

---

## Implementation Checklist

- [ ] Go Gateway: Sentry SDK initialized
- [ ] Go Gateway: Structured logging middleware
- [ ] Go Gateway: OpenTelemetry exporter (Jaeger)
- [ ] Python Agent Service: Python logging formatter (JSON)
- [ ] Python Agent Service: Sentry integration
- [ ] Database: Query duration tracking
- [ ] Redis: Operation latency tracking
- [ ] Metrics: Prometheus endpoints exposed
- [ ] Logs: Elasticsearch index templates created
- [ ] Alerts: Sentry/PagerDuty rules configured
- [ ] Health: /health endpoint implemented
- [ ] Dashboards: Kibana saved searches created
- [ ] Documentation: Runbook for common issues

---

## References

- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
- [OpenTelemetry Specification](https://opentelemetry.io/docs/reference/specification/)
- [Sentry Documentation](https://docs.sentry.io/)
- [Elasticsearch Best Practices](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [JSON Logging Standard](https://json-schema.org/)
