# WebSocket Protocol Specification

**Phase 1 Task 1.3**: Real-time communication substrate for TouchCLI

## Frame Format (JSON)

All WebSocket messages follow this envelope:

```json
{
  "type": "message" | "agent-action" | "agent-state" | "heartbeat" | "error",
  "id": "uuid-v4",
  "conversation_id": "uuid-v4",
  "timestamp": "2026-03-02T12:00:00.000Z",
  "payload": { /* type-specific content */ }
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | ✓ | Frame type indicator |
| `id` | string (UUID) | ✓ | Unique frame identifier (for deduplication) |
| `conversation_id` | string (UUID) | ✓ | Conversation context |
| `timestamp` | string (ISO 8601) | ✓ | Server-side timestamp |
| `payload` | object | ✓ | Type-specific data |

---

## Frame Types

### 1. Message (User→Agent)

**Direction**: Client → Server

```json
{
  "type": "message",
  "id": "msg-12345",
  "conversation_id": "conv-abc",
  "timestamp": "2026-03-02T12:00:00.000Z",
  "payload": {
    "content": "What's the status of the $500k deal?",
    "attachments": [
      {
        "type": "image",
        "url": "data:image/png;base64,..."
      }
    ]
  }
}
```

**Payload Fields**:
- `content` (string, 1-10000 chars): User text input or voice transcript
- `attachments` (array, optional): Files, images, or structured data

---

### 2. Agent-Action (Agent→Client)

**Direction**: Server → Client

Indicates an Agent is performing an action (taking a tool, writing to database, etc.).

```json
{
  "type": "agent-action",
  "id": "action-56789",
  "conversation_id": "conv-abc",
  "timestamp": "2026-03-02T12:00:01.000Z",
  "payload": {
    "agent_name": "Sales",
    "action_type": "tool_call",
    "action_name": "query_opportunities",
    "parameters": {
      "customer_id": "cust-123",
      "stage_filter": ["negotiation", "proposal"]
    },
    "status": "pending" | "executing" | "completed" | "failed"
  }
}
```

**Payload Fields**:
- `agent_name` (string): Router, Sales, Data, Strategy, Sentinel, Memory
- `action_type` (string): tool_call, database_write, memory_update, etc.
- `action_name` (string): Name of the action/tool being called
- `parameters` (object): Input parameters
- `status` (string): Current execution status

---

### 3. Agent-State (Agent→Client)

**Direction**: Server → Client

Updated Agent checkpoint/memory state after an action completes.

```json
{
  "type": "agent-state",
  "id": "state-99999",
  "conversation_id": "conv-abc",
  "timestamp": "2026-03-02T12:00:02.000Z",
  "payload": {
    "agent_name": "Sales",
    "checkpoint_data": {
      "state": "waiting_for_user_input",
      "context": {
        "customer_name": "ABC Corp",
        "opportunities_found": 3,
        "next_action": "recommend_strategy"
      }
    },
    "memory_update": {
      "short_term": [
        "User asked about $500k deal",
        "Found 3 active opportunities for ABC Corp"
      ],
      "long_term": {
        "customer_id": "cust-123",
        "last_interaction": "2026-03-02T12:00:00Z"
      }
    }
  }
}
```

**Payload Fields**:
- `agent_name` (string): Name of the Agent whose state changed
- `checkpoint_data` (object): LangGraph checkpoint/state serialization
- `memory_update` (object): Short-term and long-term memory changes

---

### 4. Heartbeat (Server→Client)

**Direction**: Server → Client

Sent every 30 seconds to keep connection alive.

```json
{
  "type": "heartbeat",
  "id": "hb-1704134400000",
  "conversation_id": "conv-abc",
  "timestamp": "2026-03-02T12:00:30.000Z",
  "payload": {
    "status": "ok",
    "server_time": "2026-03-02T12:00:30.000Z",
    "active_agents": ["Router", "Sales"]
  }
}
```

**Payload Fields**:
- `status` (string): "ok", "slow", or "critical"
- `server_time` (string): Current server time (for clock sync)
- `active_agents` (array): List of currently active Agent names

---

### 5. Error (Server→Client or Client→Server)

**Direction**: Either direction

Indicates protocol or business logic error.

```json
{
  "type": "error",
  "id": "err-12321",
  "conversation_id": "conv-abc",
  "timestamp": "2026-03-02T12:00:05.000Z",
  "payload": {
    "code": "AGENT_TIMEOUT",
    "message": "Sales Agent did not respond within 5 seconds",
    "recoverable": true,
    "recovery_action": "retry"
  }
}
```

**Payload Fields**:
- `code` (string): Error code (AGENT_TIMEOUT, DB_ERROR, AUTH_ERROR, etc.)
- `message` (string): Human-readable error description
- `recoverable` (boolean): Whether client should retry
- `recovery_action` (string, optional): Suggested recovery action

---

## Connection Lifecycle

### 1. Connect & Authenticate

```
Client                                  Server
  |                                        |
  |---- WebSocket UPGRADE + Bearer token --|
  |                                        |
  |<---------- 101 Switching Protocols ---|
  |                                        |
  |---- { type: "init", conversation_id } |
  |                                        |
  |<---- { type: "heartbeat", status:ok } |
```

### 2. Active Conversation

```
Client                                  Server
  |                                        |
  |---- { type: "message", content: "..." } |
  |                                        |
  |<---- { type: "agent-action", ... }    |
  |<---- { type: "agent-action", ... }    |
  |<---- { type: "agent-state", ... }     |
  |<---- { type: "message", content: "..." } |
  |                                        |
  |---- { type: "message", content: "..." } |
  |  (and so on...)                         |
```

### 3. Heartbeat (Every 30s)

```
Client                                  Server
  |                                        |
  |<------------ HEARTBEAT (30s) ----------|
  |                                        |
  |<------------ HEARTBEAT (60s) ----------|
```

### 4. Client Timeout & Reconnect

```
Client                                  Server
  |                                        |
  | (no heartbeat for 90s)                 |
  |------ CLOSE (code 1000) ------------->|
  |                                        |
  |<------ WebSocket UPGRADE + token ----->| (reconnect)
  |<------------ HEARTBEAT -----------|
```

---

## Error Codes

| Code | Meaning | Recoverable | Action |
|------|---------|-------------|--------|
| AGENT_TIMEOUT | Agent didn't respond in time | Yes | Retry with longer timeout |
| DB_ERROR | Database operation failed | Maybe | Retry or escalate |
| AUTH_ERROR | Invalid or expired token | No | Re-authenticate |
| INVALID_FRAME | Malformed JSON | No | Log & close connection |
| CONVERSATION_NOT_FOUND | Conversation ID invalid | No | Create new conversation |
| AGENT_CRASH | Agent encountered critical error | Maybe | Reset Agent state |

---

## Reconnection Strategy

```python
# Exponential backoff with jitter
backoff_delays = [1, 2, 4, 8, 16, 30]  # seconds
max_retries = 6

for attempt in range(max_retries):
    try:
        connect_websocket()
        break
    except ConnectionError:
        delay = backoff_delays[attempt] + random(0, 1)
        sleep(delay)
```

---

## Sequence Diagram: Full Conversation

```
User                   Client App              Server              Agent(Router)
  |                       |                      |                     |
  | "What deals?"         |                      |                     |
  |------- TEXT --------->|                      |                     |
  |                       |--- message frame --->|                     |
  |                       |                      |--- dispatch ------->|
  |                       |                      |                     |
  |                       |<-- agent-action |----|<-- tool_call -------|
  |                       |   (query_opps)       |                     |
  |                       |                      |--- database query -->|
  |                       |<-- agent-state |----|<-- checkpoint -------|
  |                       |   (3 opps found)     |                     |
  |                       |                      |--- delegate ------->|
  |                       |                      |                     |
  |                       |                      |--- Agent(Sales) ----|
  |                       |<-- agent-action |----|<-- analysis --------|
  |                       |<-- agent-state |----|<-- recommendation ---|
  |                       |<-- message -----|----<-- "Here are 3..." --|
  | "Here are 3..."       |                      |                     |
  |<------- TEXT---------|                      |                     |
```

---

## Testing Checklist

- [ ] Connect and receive initial heartbeat within 2s
- [ ] Send message and receive agent-action within 5s
- [ ] Receive heartbeat every 30±2s
- [ ] Disconnect due to no heartbeat after 90s
- [ ] Reconnect with exponential backoff
- [ ] Frame deduplication (same ID twice → process once)
- [ ] Concurrent messages (multiple users in same conversation)
- [ ] Agent timeout and error recovery

---

**Status**: Phase 1 Task 1.3 (Draft)
**Last Updated**: 2026-03-02
