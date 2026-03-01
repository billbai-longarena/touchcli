# Logging Standards — TouchCLI Phase 2

> **Task**: 2.4 Logging Configuration & Structured Logging
> **Status**: Reference documentation for Phase 2 implementation

## Logging Architecture

TouchCLI uses structured logging with both JSON and text formats to support development and production observability.

### Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| DEBUG | Development details, function entry/exit | LangGraph state transitions, cache hits/misses |
| INFO | Normal operations, key milestones | User login, conversation created, agent action |
| WARNING | Recoverable issues | Rate limit near threshold, optional config missing |
| ERROR | Recoverable failures | Database retry after timeout, failed API call with fallback |
| CRITICAL | System failures | Database connection lost, Redis unavailable |

### Log Format

#### JSON Format (Production)

```json
{
  "timestamp": "2026-03-02T12:34:56.789Z",
  "level": "INFO",
  "service": "agent_service",
  "correlation_id": "conv-uuid",
  "message": "Conversation created",
  "user_id": "user-uuid",
  "metadata": {
    "conversation_type": "sales",
    "agent_count": 3
  },
  "duration_ms": 125
}
```

**Fields**:
- `timestamp`: ISO 8601 UTC
- `level`: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `service`: agent_service, gateway
- `correlation_id`: Trace across requests (conversation_id, request_id, etc.)
- `message`: Human-readable log message
- `user_id`: User context (if available)
- `metadata`: Structured key-value pairs for context
- `duration_ms`: Elapsed time for operations (optional)

#### Text Format (Development)

```
2026-03-02 12:34:56 INFO [agent_service] Conversation created (conv-uuid) - user: user-uuid, type: sales, agents: 3 (125ms)
```

### Service Logging Requirements

#### FastAPI Agent Service (Python)

**Initialization Logging**:
```python
logger.info(
    "Agent service starting",
    extra={
        "database_url": settings.database_url.split("@")[1],  # Hide credentials
        "redis_url": settings.redis_url,
        "log_level": settings.log_level,
        "environment": settings.environment
    }
)
```

**Request Logging**:
```python
# Log at request start (correlation_id in context)
logger.info(
    f"{request.method} {request.url.path}",
    extra={
        "correlation_id": request.headers.get("X-Correlation-ID"),
        "user_id": request.user.id if hasattr(request, "user") else None,
        "ip": request.client.host
    }
)

# Log at response (with duration)
logger.info(
    "Request completed",
    extra={
        "correlation_id": correlation_id,
        "status_code": response.status_code,
        "duration_ms": duration
    }
)
```

**Database Operations**:
```python
logger.debug(
    "Database query",
    extra={
        "query": "SELECT * FROM conversations WHERE ...",  # Only in DEBUG
        "duration_ms": query_duration,
        "row_count": len(results)
    }
)
```

**Agent Action Logging** (LangGraph):
```python
logger.info(
    f"Agent action: {agent_name}",
    extra={
        "conversation_id": conversation_id,
        "agent_name": agent_name,
        "tool_used": tool_name,
        "state_tokens": token_count
    }
)
```

**Task Queue Logging** (Celery):
```python
logger.info(
    f"Task queued: {task_name}",
    extra={
        "task_id": task_id,
        "queue": queue_name,
        "eta": eta
    }
)

logger.info(
    f"Task completed: {task_name}",
    extra={
        "task_id": task_id,
        "duration_ms": duration,
        "result_size_bytes": len(json.dumps(result))
    }
)
```

#### Go Gateway

**Request/Response Logging**:
```go
log.Printf("[%s] %s %s -> %d (%dms) correlation_id=%s",
    time.Now().Format(time.RFC3339),
    r.Method,
    r.URL.Path,
    statusCode,
    duration,
    correlationID,
)
```

**WebSocket Logging**:
```go
log.Printf("[WS] Client %s connected from %s", clientID, clientIP)
log.Printf("[WS] Frame type=%s, conversation=%s", frameType, conversationID)
log.Printf("[WS] Client %s disconnected after %dms", clientID, duration)
```

### Structured Logging Implementation

**Python (structlog + uvicorn)**:
```python
import structlog
from pythonjsonlogger import jsonlogger

# Initialize structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Use with correlation context
with structlog.contextvars.as_immutable(correlation_id=conversation_id):
    logger.info("event", user_id=user_id, duration_ms=duration)
```

### Observability Patterns

#### Request Tracing
- All requests generate or propagate `X-Correlation-ID` header
- Header value flows through Agent→Database→Redis calls
- Used in logs for request reconstruction across services

#### Performance Monitoring
- Log duration_ms for all I/O operations (DB, Redis, API calls)
- Log token counts for LLM operations (for cost tracking)
- Log cache hit rates (e.g., "Redis hit: 85.2%")

#### Error Handling
```python
try:
    result = await agent.process(message)
except AgentError as e:
    logger.error(
        "Agent processing failed",
        exc_info=True,  # Include stack trace
        extra={
            "conversation_id": conversation_id,
            "error_code": e.code,
            "retry_count": retry_count,
            "will_retry": should_retry
        }
    )
```

### Log Retention & Rotation

**Local Development**:
- Console output (default)
- Optional file: `/tmp/touchcli/agent_service.log` (rotating, 10MB per file)

**Staging/Production**:
- Centralized logging (e.g., ELK, Datadog, CloudWatch)
- 30-day retention
- Structured JSON format with correlation IDs
- Alert on ERROR/CRITICAL levels

### Configuration Examples

**Development** (.env):
```
LOG_LEVEL=DEBUG
LOG_FORMAT=text
```

**Production** (.env):
```
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/touchcli/agent_service.log
```

---

**References**:
- Python logging: https://docs.python.org/3/library/logging.html
- structlog: https://www.structlog.org/
- Go logging: https://golang.org/pkg/log/
- Structured logging best practices: https://www.kartar.net/2015/12/structured-logging/
