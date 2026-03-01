# TouchCLI Redis Keyspace Design

**Version**: 1.0
**Created**: 2026-03-02
**Purpose**: Design of Redis keys for session state, caching, rate limiting, and real-time data

---

## Overview

Redis is used for **three purposes** in TouchCLI:

1. **Session State** (Session data, temporary conversation context)
2. **Cache Layer** (Customer/opportunity frequently accessed data)
3. **Rate Limiting** (Per-user request quotas)
4. **Real-time Queues** (BullMQ job queues for async tasks)

This document defines the namespace, expiration, and access patterns for each category.

---

## Key Naming Convention

### Format

```
<category>:<entity_type>:<entity_id>:[subkey]
```

**Example**:
- `session:conv:550e8400-e29b-41d4-a716-446655440000`
- `cache:customer:550e8400-e29b-41d4-a716-446655440000`
- `ratelimit:user:550e8400-e29b-41d4-a716:minute`

### Prefixes

| Prefix | Purpose | TTL | Data Type |
|--------|---------|-----|-----------|
| `session:` | Session & conversation state | 24 hours | Hash, String, List |
| `cache:` | Read-through cache for expensive queries | 1 hour | Hash, JSON (String) |
| `ratelimit:` | Request rate counters | 1 minute/hour | Integer |
| `lock:` | Distributed locks for critical sections | 10 seconds | String (flag) |
| `queue:` | BullMQ job queues | Varies | Serialized JSON |
| `index:` | Secondary indexes for search | Varies | Set, SortedSet |
| `temp:` | Temporary processing data | 5-30 minutes | Various |

---

## Session State (`session:`)

### Conversation Session

**Key**: `session:conv:<conversation_id>`

**Type**: Hash

**Fields**:
```redis
HSET session:conv:550e8400-... \
  user_id "user-uuid" \
  customer_id "customer-uuid" \
  opportunity_id "opportunity-uuid" \
  mode "text|voice|hybrid" \
  status "active|completed" \
  router_state '{"stage": "intent_detection", "confidence": 0.95}' \
  context '{"last_message_at": "2026-03-02T12:00:00Z", "message_count": 5}' \
  created_at "2026-03-02T12:00:00Z"
```

**TTL**: 24 hours (auto-renewed on every message)

**Access Pattern**:
```python
# Get conversation session
session = redis.hgetall('session:conv:conv-uuid')

# Update conversation context
redis.hset('session:conv:conv-uuid', 'router_state', json.dumps(state))
```

---

### User Session

**Key**: `session:user:<user_id>`

**Type**: Hash

**Fields**:
```redis
HSET session:user:user-uuid \
  jwt_token "eyJhbGc..." \
  refresh_token "..." \
  login_time "2026-03-02T08:00:00Z" \
  ip_address "192.168.1.1" \
  user_agent "Mozilla/5.0..." \
  active_conversations '[conv-uuid-1, conv-uuid-2]' \
  preference_language "zh" \
  preference_timezone "Asia/Shanghai"
```

**TTL**: 7 days (login session)

**Access Pattern**:
```python
# Check if user is logged in
exists = redis.exists('session:user:user-uuid')

# Get active conversations for user
convs = redis.hget('session:user:user-uuid', 'active_conversations')
```

---

## Cache Layer (`cache:`)

### Customer Data Cache

**Key**: `cache:customer:<customer_id>`

**Type**: Hash (or String with JSON)

**Fields**:
```redis
HSET cache:customer:customer-uuid \
  name "张总" \
  type "company" \
  phone "13800000000" \
  email "zhang@company.com" \
  assigned_to "user-uuid" \
  opportunities '[opp-uuid-1, opp-uuid-2]' \
  tags '[tag1, tag2]' \
  last_interaction "2026-03-02T10:00:00Z"
```

**TTL**: 1 hour (invalidated on update)

**Access Pattern**:
```python
# Get cached customer (fallback to DB if miss)
cached = redis.hgetall('cache:customer:customer-uuid')
if not cached:
    cached = db.query(Customer).find(customer_uuid)
    redis.hset('cache:customer:customer-uuid', mapping=cached)
    redis.expire('cache:customer:customer-uuid', 3600)
```

---

### Opportunity Data Cache

**Key**: `cache:opp:<opportunity_id>`

**Type**: Hash

**Fields**:
```redis
HSET cache:opp:opp-uuid \
  name "500K Deal" \
  customer_id "customer-uuid" \
  amount "500000" \
  status "proposal" \
  probability "0.75" \
  expected_close "2026-04-01" \
  last_updated "2026-03-02T12:00:00Z"
```

**TTL**: 1 hour

---

## Rate Limiting (`ratelimit:`)

### User Message Rate Limit

**Key**: `ratelimit:user:<user_id>:minute`

**Type**: Integer (counter)

**Usage**:
```redis
INCR ratelimit:user:user-uuid:minute
EXPIRE ratelimit:user:user-uuid:minute 60

# If count > 100, reject request (100 messages per minute)
```

**Limits**:
- **Per minute**: 100 messages
- **Per hour**: 1000 messages
- **Per day**: 10000 messages

---

### API Rate Limit (by IP)

**Key**: `ratelimit:ip:<ip_address>:hour`

**Type**: Integer

**Usage**:
```redis
# Check before processing
count = redis.incr(f'ratelimit:ip:{ip}:hour')
if count == 1:
    redis.expire(f'ratelimit:ip:{ip}:hour', 3600)

if count > 10000:  # 10k requests per hour
    return 429 Too Many Requests
```

---

## Distributed Locks (`lock:`)

### Database Migration Lock

**Key**: `lock:db:migration`

**Type**: String (lock token)

**Usage**:
```python
# Acquire lock (auto-release after 10 seconds)
lock = redis.set('lock:db:migration', 'worker-1-pid', ex=10, nx=True)
if lock:
    # Do migration
    db.migrate()
    redis.delete('lock:db:migration')
else:
    # Lock held by other worker, retry
    time.sleep(1)
```

**TTL**: 10 seconds (auto-release to prevent deadlock)

---

### Agent Execution Lock

**Key**: `lock:agent:<agent_type>:<conversation_id>`

**Type**: String (agent PID)

**Usage**:
```
Prevent multiple agents from modifying same conversation state simultaneously
```

**TTL**: 30 seconds

---

## BullMQ Job Queues (`queue:`)

### Job Queue Names

| Queue | Purpose | Workers |
|-------|---------|---------|
| `queue:notifications` | Send email/SMS/push notifications | 2 workers |
| `queue:exports` | Generate CSV/PDF exports | 1 worker |
| `queue:data-sync` | Sync with external CRM systems | 1 worker |
| `queue:webhooks` | Deliver webhooks to integrations | 2 workers |

### Queue Data Structure

BullMQ automatically manages queue data. Key patterns:

```redis
# Job registry (managed by BullMQ)
queue:notifications:jobs  # hash of job_id -> job_data
queue:notifications:active  # set of active job ids
queue:notifications:completed  # set of completed job ids
queue:notifications:failed  # set of failed job ids
queue:notifications:delayed  # sorted set with delay times

# Scheduled/delayed jobs
queue:notifications:paused-count  # count of paused jobs
queue:notifications:repeat  # hash of recurring job configs
```

### Job Payload Example

```json
{
  "id": "notification-1234",
  "type": "send_email",
  "data": {
    "user_id": "user-uuid",
    "template": "opportunity_created",
    "variables": {
      "customer_name": "Zhang",
      "amount": "500000"
    }
  },
  "priority": 5,
  "attempts": 0,
  "maxAttempts": 3,
  "backoff": "exponential",
  "delay": 0,
  "timestamp": 1709384400000
}
```

---

## Secondary Indexes (`index:`)

### Customer Search Index (by phone)

**Key**: `index:customer:phone:<phone_hash>`

**Type**: Set

**Usage**:
```redis
SADD index:customer:phone:138000... customer-uuid-1 customer-uuid-2

# Fast phone lookup
customer_ids = redis.smembers('index:customer:phone:138000...')
```

---

### Opportunity Status Index

**Key**: `index:opp:status:<status>`

**Type**: Set

**Usage**:
```redis
SADD index:opp:status:proposal opp-uuid-1 opp-uuid-2 opp-uuid-3

# Quick count of opportunities in "proposal" stage
count = redis.scard('index:opp:status:proposal')
```

**TTL**: Invalidated when opportunity status changes

---

### User Active Conversations

**Key**: `index:user:active_convs:<user_id>`

**Type**: Set

**Usage**:
```redis
SADD index:user:active_convs:user-uuid conv-uuid-1 conv-uuid-2

# Invalidate on conversation close
SREM index:user:active_convs:user-uuid conv-uuid-2
```

---

## Temporary Data (`temp:`)

### Message Processing Pipeline

**Key**: `temp:msg:processing:<message_id>`

**Type**: String (JSON)

**Purpose**: Store intermediate processing state

**Data**:
```json
{
  "message_id": "msg-uuid",
  "conversation_id": "conv-uuid",
  "original_content": "...",
  "transcribed_content": "...",
  "intent": "create_opportunity",
  "confidence": 0.92,
  "route_to_agent": "sales",
  "status": "intent_detected"
}
```

**TTL**: 5 minutes (sufficient for processing, auto-cleanup)

---

### Agent Checkpoint (Temporary)

**Key**: `temp:agent:checkpoint:<conversation_id>:<agent_type>`

**Type**: String (JSON)

**Purpose**: Cache LangGraph checkpoint during execution

**Data**:
```json
{
  "conversation_id": "conv-uuid",
  "agent_type": "router",
  "state": { ... },
  "messages": [ ... ],
  "tools_available": [ ... ],
  "checkpoint_id": "chk-123",
  "timestamp": "2026-03-02T12:00:00Z"
}
```

**TTL**: 10 minutes

---

## Data Expiration & Cleanup

| Category | TTL | Cleanup Strategy |
|----------|-----|------------------|
| `session:conv:*` | 24 hours | Auto-expire on TTL |
| `session:user:*` | 7 days | Auto-expire on TTL |
| `cache:*` | 1 hour | Invalidate on write, auto-expire |
| `ratelimit:*` | 1-60 minutes | Auto-expire |
| `lock:*` | 10 seconds | Auto-expire |
| `queue:*` | Varies | BullMQ-managed |
| `index:*` | Varies | Invalidate on updates |
| `temp:*` | 5-30 minutes | Auto-expire |

---

## Performance & Sizing

### Memory Estimation

**Assumptions**:
- 10,000 active users
- 1,000 concurrent conversations
- Average data per entity: 500 bytes

**Calculation**:
- Session state: 10K users × 500B = 5 MB
- Conversation state: 1K convs × 1 KB = 1 MB
- Customer cache: 10K customers × 500B = 5 MB
- Opportunity cache: 50K opportunities × 500B = 25 MB
- Rate limiting counters: 10K × 8B = 80 KB
- **Total**: ~36 MB (reasonable for Redis)

### Redis Configuration

```ini
# redis.conf
maxmemory 256mb  # or higher depending on load
maxmemory-policy allkeys-lru  # evict least recently used keys
appendonly yes  # durability (RDB snapshots + AOF)
save 900 1  # save if 1 change in 900 seconds
save 300 10  # save if 10 changes in 300 seconds
```

---

## Operational Monitoring

### Key Metrics

1. **Hit Rate**: `cache:customer:*` and `cache:opp:*`
   - Target: > 80% cache hit ratio

2. **Memory Usage**: Total Redis memory
   - Alert if > 80% of maxmemory

3. **Key Eviction Rate**: If LRU eviction happening
   - Alert if > 1000 evictions/minute

4. **Rate Limit Violations**: Count of rejected requests
   - Track per user_id, per IP

### Debugging Commands

```redis
# List all keys by pattern
KEYS cache:customer:*
KEYS session:conv:*

# Monitor key access in real-time
MONITOR

# Analyze memory usage
DEBUG OBJECT cache:customer:uuid

# Check expiration times
TTL session:conv:uuid
```

---

## Security Considerations

1. **Sensitive Data**: Tokens and PII stored in Redis should be encrypted at rest
2. **Access Control**: Restrict Redis to internal network (not internet-facing)
3. **Persistence**: Enable RDB snapshots + AOF for data durability
4. **Expiration**: All keys have explicit TTL to prevent accumulation

---

## Future Enhancements

- [ ] Redis Cluster for horizontal scaling
- [ ] Redis Sentinel for HA failover
- [ ] Encryption at rest (Redis 6.0+ ACL)
- [ ] Stream-based message log (instead of queuing)
- [ ] Bloom filters for fast negative lookups
