# Redis Cache & Session Design

**Phase 1 Task 1.4**: Cache strategy and session state management

---

## Overview

Redis serves as the high-speed cache and session store for TouchCLI backend. It reduces database load, speeds up Agent response times, and maintains WebSocket session state.

### Key Principles

1. **Cache-Aside Pattern**: Application checks Redis first, then database
2. **TTL Management**: All keys expire automatically (no manual cleanup)
3. **Atomic Operations**: Use Redis transactions for critical updates
4. **LRU Eviction**: Set maxmemory-policy to "allkeys-lru"
5. **Single Source of Truth**: DB is the master; Redis is ephemeral

---

## Key Namespaces

### 1. Session Management

**Prefix**: `session:{session_id}`

```
session:550e8400-e29b-41d4-a716-446655440000
  -> {
    "user_id": "user-123",
    "conversation_id": "conv-456",
    "websocket_connected": true,
    "last_heartbeat": 1709470800,
    "agent_states": {...},
    "temp_data": {...}
  }

TTL: 3600 seconds (1 hour active session)
     → Auto-extend on each heartbeat
```

**Operations**:
```bash
SET session:$sid <json> EX 3600
GET session:$sid
DEL session:$sid (on logout)
EXPIRE session:$sid 3600 (on heartbeat)
```

---

### 2. Customer Data Cache

**Prefix**: `cache:customer:{customer_id}`

```
cache:customer:cust-abc-123
  -> {
    "id": "cust-abc-123",
    "company_name": "ABC Corp",
    "industry": "Healthcare",
    "region": "US-West",
    "classification": "VIP",
    "total_revenue": 500000,
    "active_opportunities": 3,
    "last_interaction": "2026-03-01T15:30:00Z"
  }

TTL: 3600 seconds (1 hour)
```

**Operations**:
```bash
# Refresh from DB every hour
SET cache:customer:$cid <full_json> EX 3600
GETEX cache:customer:$cid EX 3600 (refresh TTL on access)

# Invalidate on customer update
DEL cache:customer:$cid
```

---

### 3. User Preferences & Settings

**Prefix**: `cache:user:{user_id}`

```
cache:user:user-456
  -> {
    "id": "user-456",
    "name": "Alice Chen",
    "role": "salesperson",
    "preferences": {
      "language": "en",
      "timezone": "US/Pacific",
      "notifications_enabled": true
    },
    "agent_config": {
      "risk_tolerance": "medium",
      "auto_logging": true
    }
  }

TTL: 7200 seconds (2 hours)
```

**Operations**:
```bash
SET cache:user:$uid <json> EX 7200
HGET cache:user:$uid preferences
HSET cache:user:$uid agent_config '{"risk_tolerance": "high"}'
```

---

### 4. Rate Limiting

**Prefix**: `ratelimit:{user_id}`

```
ratelimit:user-456
  -> {
    "message_count": 45,
    "window_start": 1709470800,
    "reset_at": 1709474400  (1 hour window)
  }

TTL: 3600 seconds (1 hour)
      → Resets automatically
```

**Operations**:
```bash
# Increment counter
INCR ratelimit:$uid:messages

# Check against limit (e.g., 100 msgs/hour)
GET ratelimit:$uid:messages
  -> if > 100: reject request

# Expire window
EXPIRE ratelimit:$uid:messages 3600
```

**Rate Limit Rules**:
- **Messages**: 100 per user per hour
- **API calls**: 1000 per user per hour
- **Tool calls**: 500 per conversation per hour

---

### 5. Agent Checkpoint Buffer

**Prefix**: `agent:checkpoint:{conversation_id}`

```
agent:checkpoint:conv-789
  -> {
    "router_state": {...LangGraph checkpoint...},
    "sales_agent_state": {...},
    "data_agent_state": {...},
    "memory": {
      "short_term": ["User asked about deals", "3 opps found"],
      "long_term": {
        "customer_id": "cust-123",
        "interaction_count": 5
      }
    },
    "timestamp": 1709470800
  }

TTL: 86400 seconds (24 hours, or until conversation ends)
     → Deleted on conversation.ended_at
```

**Operations**:
```bash
# Update after each Agent action
HSET agent:checkpoint:$conv_id router_state <json>
HSET agent:checkpoint:$conv_id memory <json>

# Retrieve full checkpoint
HGETALL agent:checkpoint:$conv_id

# Update TTL when conversation ends
DEL agent:checkpoint:$conv_id
```

---

### 6. Message Queue (BullMQ Integration)

**Prefix**: `bull:queue:{queue_name}`

```
bull:queue:agent_tasks
  -> Job queue for async Agent processing

bull:queue:notifications
  -> Job queue for real-time user notifications
```

Each job has:
```json
{
  "id": "job-123",
  "data": { "conversation_id": "...", "action": "..." },
  "status": "pending" | "active" | "completed" | "failed",
  "attempts": 0,
  "delay": 0
}
```

---

### 7. Conversation Lock (Mutex)

**Prefix**: `lock:conversation:{conversation_id}`

```
lock:conversation:conv-789 = "agent-router-process-id"

TTL: 30 seconds (auto-release if Agent crashes)
```

**Operations**:
```bash
# Acquire lock (only one Agent can process conversation at a time)
SET lock:$conv_id $process_id EX 30 NX
  -> OK or nil

# Release lock when done
DEL lock:$conv_id

# Extend lock if still processing
EXPIRE lock:$conv_id 30
```

---

## Connection Configuration

```python
# Python + Redis
import redis

redis_client = redis.Redis(
    host='localhost',      # or redis://redis-service:6379
    port=6379,
    db=0,
    decode_responses=True  # return strings, not bytes
)

# Connection pool for performance
redis_pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,
    retry_on_timeout=True
)
client = redis.Redis(connection_pool=redis_pool)

# Health check
try:
    redis_client.ping()
    print("Redis OK")
except redis.ConnectionError:
    print("Redis unavailable")
```

---

## Eviction Policy

```bash
# redis.conf
maxmemory 1gb
maxmemory-policy allkeys-lru

# Rationale:
# - Least Recently Used evicts oldest accessed keys
# - Allows full keyspace eviction (not just expiring keys)
# - Prevents "OOM command not allowed" errors
```

---

## Monitoring & Metrics

```bash
# Monitor key space
DBSIZE                          # Total keys in DB
INFO memory                     # Memory usage stats
INFO stats                      # Hit/miss rates

# Example alert: Hit rate < 80%
HITS = INFO stats | keyspace_hits
MISSES = INFO stats | keyspace_misses
HIT_RATE = HITS / (HITS + MISSES)
  -> Alert if < 0.8
```

---

## Development Examples

### Example 1: Cache Customer Data

```python
# Check cache
customer = redis_client.get(f"cache:customer:{customer_id}")
if not customer:
    # Cache miss, fetch from DB
    customer = db.customers.get(customer_id)
    redis_client.set(
        f"cache:customer:{customer_id}",
        json.dumps(customer),
        ex=3600
    )
return customer
```

### Example 2: Rate Limit Check

```python
key = f"ratelimit:{user_id}:messages"
count = redis_client.incr(key)
redis_client.expire(key, 3600)  # 1 hour window

if count > 100:
    raise RateLimitError("Too many messages")
```

### Example 3: Agent Checkpoint Storage

```python
checkpoint = {
    "state": agent.state,
    "memory": agent.memory,
    "timestamp": time.time()
}

redis_client.hset(
    f"agent:checkpoint:{conversation_id}",
    "router_state",
    json.dumps(checkpoint)
)
redis_client.expire(f"agent:checkpoint:{conversation_id}", 86400)
```

### Example 4: Conversation Lock

```python
import time

def acquire_lock(conversation_id, process_id, timeout=30):
    lock_key = f"lock:conversation:{conversation_id}"
    if redis_client.set(lock_key, process_id, ex=timeout, nx=True):
        return True
    return False

def release_lock(conversation_id, process_id):
    lock_key = f"lock:conversation:{conversation_id}"
    if redis_client.get(lock_key) == process_id:
        redis_client.delete(lock_key)

# Usage
if acquire_lock("conv-789", "router-process-1"):
    try:
        # Process conversation
        ...
    finally:
        release_lock("conv-789", "router-process-1")
```

---

## Backup & Persistence

```bash
# Periodic snapshots (RDB)
SAVE                      # Blocking snapshot
BGSAVE                    # Non-blocking background save

# OR: AOF (append-only file)
# redis.conf
appendonly yes
appendfsync everysec

# Both: RDB for speed, AOF for durability
```

---

## Testing Checklist

- [ ] Can connect to Redis with connection pool
- [ ] SET and GET operations work
- [ ] TTL expiration works (test with SHORT TTL)
- [ ] INCR counters for rate limiting
- [ ] HSET/HGET for structured data
- [ ] Lock acquire/release (test concurrent access)
- [ ] Eviction policy prevents OOM (test with large keys)
- [ ] Memory usage < 1GB under normal load

---

**Status**: Phase 1 Task 1.4 (Draft)
**Last Updated**: 2026-03-02
