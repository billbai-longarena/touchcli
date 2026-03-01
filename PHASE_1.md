# Phase 1: Backend Foundation — Data & Communication Substrate

> **Status**: 🔴 IN PROGRESS (Worker phase, S-002 claimed)
> **Timeline**: 4-6 weeks
> **Signal**: S-002 (w:48 IMPLEMENT)
> **Caste**: Worker
> **Worker ID**: termite-1772386089-46104

---

## Overview

Phase 1 establishes the foundational data layer and communication protocols for TouchCLI backend. All Agent systems (Phase 2+) depend on this layer.

## Task Breakdown

### Task 1.1: PostgreSQL Schema Design

**Objective**: Define relational schema for all core entities.

**Subtasks**:
- [ ] users table (id, email, name, avatar_url, created_at, updated_at)
- [ ] customers table (user_id, company, region, classification, metadata_json, created_at)
- [ ] opportunities table (id, customer_id, amount, stage, expected_close, agent_notes_json)
- [ ] conversations table (id, user_id, started_at, ended_at, summary_text, agent_states_json)
- [ ] messages table (id, conversation_id, sender_type, content, attachments_json, timestamp)
- [ ] agent_states table (id, conversation_id, agent_name, checkpoint_data_json, version, updated_at)

**Design Principles**:
- Immutable audit columns: created_at, updated_by, version
- JSON columns for semi-structured data (metadata, checkpoints)
- Indexes on foreign keys, timestamps, frequently-queried fields
- Support for full-text search on conversations/messages

**Deliverables**:
- `schema.sql` — complete SQL DDL
- `migrations/` directory with Alembic templates

---

### Task 1.2: API Interface Definition (OpenAPI 3.0)

**Objective**: Define REST API contract for all client→backend communication.

**Core Endpoints**:
- `POST /conversations` — start new conversation
- `POST /messages` — send message (text or voice transcript)
- `GET /messages/{conversation_id}` — fetch conversation history
- `POST /opportunities` — create/update opportunity
- `GET /opportunities?filter=stage,user_id` — query opportunities
- `GET /users/{id}` — fetch user profile

**Design Principles**:
- Request/response envelope with status codes
- Async task tracking (for long-running Agent operations)
- Pagination for list endpoints
- Error codes mapped to Agent failure modes

**Deliverables**:
- `openapi.yaml` — complete OpenAPI 3.0 spec
- `docs/api.md` — human-readable endpoint reference

---

### Task 1.3: WebSocket Protocol & Heartbeat

**Objective**: Define real-time message frame format for Agent↔Client.

**Frame Format**:
```json
{
  "type": "message" | "agent-action" | "agent-state" | "heartbeat" | "error",
  "id": "uuid-4",
  "timestamp": "2026-03-02T12:00:00Z",
  "conversation_id": "uuid",
  "payload": { /* type-specific data */ }
}
```

**Heartbeat Strategy**:
- Interval: 30s (server→client keep-alive)
- Timeout: no heartbeat for 90s → auto-reconnect
- Backoff: exponential (1s, 2s, 4s, 8s, 16s max)

**Deliverables**:
- `websocket_spec.md` — frame definitions, sequences, error handling
- `websocket_types.ts` — TypeScript interfaces (for frontend reference)

---

### Task 1.4: Redis Cache & Session Design

**Objective**: Define cache strategy for high-frequency reads & session state.

**Key Namespaces**:
- `session:{session_id}` — active WebSocket session metadata
- `cache:customer:{id}` — denormalized customer profile (TTL: 1 hour)
- `cache:user:{id}` — user preferences & settings (TTL: 1 hour)
- `ratelimit:{user_id}` — message rate limit counter (TTL: 60s)
- `agent:checkpoint:{conversation_id}` — LangGraph checkpoint buffer

**Eviction Policy**: LRU, 100MB max memory per pod

**Deliverables**:
- `redis_schema.md` — key namespace definitions, TTL rules
- `redis_cli_examples.md` — sample commands for operations

---

## Acceptance Criteria

### Code Quality
- [ ] All SQL is normalized (3NF minimum)
- [ ] All API endpoints validated against OpenAPI spec
- [ ] All error codes documented with recovery steps
- [ ] WebSocket frames pass JSON schema validation

### Documentation
- [ ] `schema.sql` compiles without errors
- [ ] OpenAPI spec passes validation (swagger-cli)
- [ ] WebSocket frame examples execute without errors
- [ ] Redis key patterns documented and tested

### Testing
- [ ] All schema migrations reversible
- [ ] All API endpoints callable with sample payloads
- [ ] WebSocket connections stable for 5+ minute heartbeat cycles
- [ ] Redis operations idempotent

---

## Dependencies

- **Blocked by**: None (Phase 1 is independent)
- **Blocks**: S-003 (Phase 2 backend infrastructure)

## Next Phase (S-003)

- Implement API server (FastAPI/Python or Gin/Go)
- Implement WebSocket server
- Deploy PostgreSQL + Redis
- Integrate with LangGraph Agent framework

---

**Worker Session**: 2026-03-02
**Status**: Foundation established, Task 1.1 to begin

