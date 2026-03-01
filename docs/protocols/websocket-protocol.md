# TouchCLI WebSocket Protocol

**Version**: 1.0
**Status**: Specification
**Created**: 2026-03-02

---

## Overview

The WebSocket protocol handles **real-time, bidirectional communication** between the client (browser/mobile) and the Gateway (Go server). The protocol is designed for:

1. **Low-latency message delivery** (target < 100ms round-trip)
2. **Audio streaming** (voice input/output)
3. **Agent action notifications** (proactive updates)
4. **Graceful reconnection** (automatic recovery)

---

## Connection

### URL Format

```
wss://api.touchcli.local:8443/ws?conversation_id=<uuid>&token=<jwt>
```

**Query Parameters**:
- `conversation_id` (required): UUID of the conversation
- `token` (required): JWT access token from previous OAuth authentication
- `client_id` (optional): Unique client identifier for reconnection tracking

### Connection Lifecycle

```
Client                                    Gateway
  |                                         |
  +------ WebSocket Upgrade Request ------>|
  |       (with Authorization header)      |
  |                                         |
  |<----- 101 Switching Protocols --------+
  |       (Connection established)         |
  |                                         |
  +-- Send "hello" frame (optional) ------>|
  |                                         |
  |<-- Receive "connected" frame ----------+
  |    (includes server_time, heartbeat_interval)
  |                                         |
  +---- Periodic heartbeat (30s) --------->|
  |                                         |
  |<---- Heartbeat ACK frame --------------+
  |                                         |
  +-- Send message frames --------------->|
  |                                         |
  |<-- Receive message/action frames -----+
  |                                         |
  +--- Close frame (or timeout) ---------->|
  |                                         |
```

---

## Frame Format

All frames are JSON objects sent as WebSocket text messages.

### Base Frame Structure

```json
{
  "type": "message | action | heartbeat | error | system",
  "id": "frame-uuid",
  "timestamp": "2026-03-02T12:00:00Z",
  "seq": 1,
  "payload": { ... }
}
```

**Fields**:
- `type` (string, required): Frame type (see below)
- `id` (string, UUID): Unique frame identifier for deduplication
- `timestamp` (string, ISO 8601): Server timestamp when frame is created
- `seq` (integer): Sequence number (monotonic, for ordering)
- `payload` (object): Type-specific data

---

## Frame Types

### 1. Message Frame

Sent by **user** or **agent** with conversational content.

**From Client (User)**:
```json
{
  "type": "message",
  "id": "msg-1234-5678",
  "timestamp": "2026-03-02T12:00:00Z",
  "seq": 1,
  "payload": {
    "role": "user",
    "content": "帮我给张总创建一个 50 万的商机",
    "content_type": "text",
    "metadata": {
      "language": "zh",
      "client_version": "1.0.0"
    }
  }
}
```

**From Server (Agent Response)**:
```json
{
  "type": "message",
  "id": "msg-9876-5432",
  "timestamp": "2026-03-02T12:00:01Z",
  "seq": 2,
  "payload": {
    "role": "agent",
    "agent_name": "router",
    "content": "我来帮你创建这个商机。先确认一下张总的客户信息...",
    "content_type": "text",
    "metadata": {
      "confidence": 0.95,
      "language": "zh"
    }
  }
}
```

---

### 2. Action Frame

Sent by **server** to notify of agent actions being executed.

```json
{
  "type": "action",
  "id": "act-5678-1234",
  "timestamp": "2026-03-02T12:00:02Z",
  "seq": 3,
  "payload": {
    "action_type": "create_opportunity",
    "action_id": "action-uuid",
    "status": "executing",
    "agent_name": "sales",
    "progress_percent": 45,
    "details": {
      "customer_name": "Zhang",
      "opportunity_name": "500k Deal",
      "amount": 500000,
      "currency": "CNY"
    },
    "estimated_completion_ms": 2000
  }
}
```

**Action Statuses**:
- `pending`: Queued, awaiting execution
- `executing`: Currently running
- `completed`: Successfully finished
- `failed`: Encountered an error
- `cancelled`: User or system cancelled

**Common Action Types**:
- `create_customer`
- `update_customer`
- `create_opportunity`
- `update_opportunity`
- `execute_query`
- `send_notification`
- `export_data`

---

### 3. Audio Frame

Sent by **client** for voice input; sent by **server** for voice output.

**From Client (Voice Input)**:
```json
{
  "type": "audio",
  "id": "audio-1234-5678",
  "timestamp": "2026-03-02T12:00:00Z",
  "seq": 4,
  "payload": {
    "direction": "input",
    "encoding": "base64",
    "format": "wav",
    "sample_rate": 16000,
    "channels": 1,
    "duration_ms": 5000,
    "chunk_sequence": 1,
    "is_final": false,
    "data": "UklGRi5C..."
  }
}
```

**From Server (Voice Output)**:
```json
{
  "type": "audio",
  "id": "audio-9876-5432",
  "timestamp": "2026-03-02T12:00:03Z",
  "seq": 5,
  "payload": {
    "direction": "output",
    "encoding": "base64",
    "format": "wav",
    "sample_rate": 24000,
    "channels": 1,
    "duration_ms": 3000,
    "chunk_sequence": 1,
    "is_final": true,
    "data": "UklGRi5D..."
  }
}
```

**Audio Streaming**:
- Streaming in chunks (not entire file at once)
- `chunk_sequence`: Sequential number for chunk ordering
- `is_final`: true when final chunk sent

---

### 4. Heartbeat Frame

Sent periodically to keep connection alive and detect disconnections.

**From Client**:
```json
{
  "type": "heartbeat",
  "id": "hb-1234-5678",
  "timestamp": "2026-03-02T12:00:30Z",
  "seq": 10,
  "payload": {
    "client_id": "client-uuid",
    "ping": true
  }
}
```

**From Server (Response)**:
```json
{
  "type": "heartbeat",
  "id": "hb-9876-5432",
  "timestamp": "2026-03-02T12:00:30Z",
  "seq": 11,
  "payload": {
    "pong": true,
    "server_time": "2026-03-02T12:00:30Z"
  }
}
```

**Heartbeat Schedule**:
- **Client sends heartbeat**: Every 30 seconds
- **Server response timeout**: 5 seconds (client closes if no response)
- **Server inactivity timeout**: 2 minutes (server closes if no client message)

---

### 5. Error Frame

Sent by **server** when an error occurs.

```json
{
  "type": "error",
  "id": "err-5678-1234",
  "timestamp": "2026-03-02T12:00:05Z",
  "seq": 6,
  "payload": {
    "error_code": "AGENT_TIMEOUT",
    "error_message": "Agent execution exceeded 30-second timeout",
    "severity": "warning",
    "related_action_id": "action-uuid",
    "recovery_suggestion": "Retry the action or contact support"
  }
}
```

**Error Codes**:
- `AUTH_EXPIRED`: JWT token expired, reconnect required
- `RATE_LIMIT`: Too many requests, slow down
- `AGENT_TIMEOUT`: Agent took too long to respond
- `AGENT_FAILED`: Agent encountered an error
- `DATABASE_ERROR`: Database operation failed
- `VALIDATION_ERROR`: Invalid request format
- `INTERNAL_ERROR`: Server internal error

---

### 6. System Frame

Sent by **server** for system-level notifications.

```json
{
  "type": "system",
  "id": "sys-1234-5678",
  "timestamp": "2026-03-02T12:00:00Z",
  "seq": 0,
  "payload": {
    "event": "connected | maintenance | shutdown | agent_available",
    "message": "Server is performing maintenance, service will be back online in 5 minutes",
    "severity": "info"
  }
}
```

---

## Message Flow Examples

### Example 1: Simple Text Conversation

```
Client                            Server (Gateway)        Agents
  |                                   |                      |
  +-- POST /conversations ----------->|                      |
  |    (create conversation)          |                      |
  |<-- conversation_id + ws_url ------+                      |
  |                                    |                      |
  +-- WebSocket Connect ------------->|                      |
  |    (with conversation_id)         |                      |
  |<-- "connected" system frame ------+                      |
  |                                    |                      |
  +-- Send "message" frame ---------->|                      |
  |    "帮我给张总创建商机"             |                      |
  |                                    +-- Router Agent ----->|
  |                                    |   (Intent detection) |
  |                                    |<-- Route to Sales --+
  |                                    |                      |
  |<-- "action" frame (executing) ----+                      |
  |    "Creating opportunity..."       |                      |
  |                                    +-- Sales Agent ------>|
  |                                    |   (Check customer)   |
  |                                    +-- Data Agent ------->|
  |                                    |   (Query DB)         |
  |                                    |<-- Customer found ---+
  |                                    |                      |
  |<-- "action" frame (completed) ----+                      |
  |    "机会已创建，ID: xxx"           |                      |
  |                                    |                      |
  +-- Send heartbeat ------------------>|                      |
  |<-- Heartbeat ACK ------------------+
```

### Example 2: Voice Input + Agent Action

```
Client                            Server              Agents
  |                                 |                   |
  +-- Audio frame (voice) -------->|                   |
  |    "帮我..."                    |                   |
  |                                 +-- Whisper API -->|
  |                                 |<-- "帮我..." -----+
  |                                 |                   |
  |<-- "message" frame (transcribed)|                   |
  |    (what user said)             |                   |
  |                                 +-- Router ------->|
  |<-- "action" frame (executing)   |                   |
  |<-- "audio" frame (TTS) ---------|                   |
  |    (Agent voice response)       |
  |<-- "action" frame (completed)   |
```

---

## Error Handling

### Reconnection Strategy

**Exponential Backoff**:
```
Attempt 1: 1 second
Attempt 2: 2 seconds
Attempt 3: 4 seconds
Attempt 4: 8 seconds
Attempt 5: 16 seconds
... (max 5 minutes)
```

### Frame Deduplication

Server maintains a **deduplication window** (last 1000 frames, ~30 minutes).

If client receives duplicate `id`, it:
1. Ignores the duplicate
2. Checks if it has processed the original
3. Sends ACK if needed

### State Recovery

On reconnection, client should:
1. Request message history since last received `seq`
2. Request agent state snapshot
3. Resume conversation from last checkpoint

---

## Security

### Authorization

- **Header**: `Authorization: Bearer <jwt_token>`
- **Token Expiration**: Access tokens valid for 1 hour
- **Refresh**: Use refresh token to obtain new access token
- **Scope**: Token includes user ID, roles, rate limit quota

### Data Protection

- **Transport**: TLS 1.3 (wss://, not ws://)
- **Confidentiality**: All frames are encrypted in transit
- **Integrity**: JWT signature verifies frame authenticity
- **Rate Limiting**: Per-user message quota (100 messages/minute)

### Input Validation

- Frame size limit: 1 MB (for audio streaming)
- Content validation: UTF-8 text, valid JSON
- Action validation: Only authorized agents can execute actions

---

## Performance Targets

| Metric | Target | SLA |
|--------|--------|-----|
| Connection establishment | < 200ms | 99.9% |
| Message latency (text) | < 100ms | 99% |
| Audio latency (round-trip) | < 500ms | 95% |
| Frame processing throughput | 1000 frames/sec | per server |
| Connection availability | > 99.95% uptime | monthly |

---

## Future Extensions

- [ ] Binary frame format (for reduced bandwidth)
- [ ] Compression (gzip for large frames)
- [ ] End-to-end encryption (optional)
- [ ] Broadcast channels (multi-agent collaboration)
- [ ] Subscription model (subscribe to user/customer events)
