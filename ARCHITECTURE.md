# TouchCLI Architecture & System Design

**Version**: 1.0
**Last Updated**: 2026-03-02
**Status**: Production-Ready

---

## Executive Summary

TouchCLI is a **real-time conversational CRM dashboard** that enables sales teams to manage customers, opportunities, and conversations through an intuitive chat interface. The system features a three-tier architecture with real-time WebSocket support, production-grade security, and comprehensive monitoring.

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture Diagram

```
┌────────────────────────────────────────────────────────────┐
│                     Browser / Mobile Client                 │
│                    (WebSocket + HTTPS)                      │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   Frontend (React SPA)     │ Port 3000/80/443
        │   - React 18 + TypeScript  │
        │   - Zustand state mgmt     │
        │   - WebSocket client       │
        │   - Nginx static serving   │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  Gateway (Go)              │ Port 8080
        │  - HTTP proxy              │
        │  - WebSocket proxy         │
        │  - Load balancing          │
        │  - CORS validation         │
        │  - Request logging         │
        └────────────┬───────────────┘
                     │
        ┌────────────┴─────────────────┐
        │                              │
        ▼                              ▼
  ┌─────────────────────┐     ┌─────────────────────┐
  │  Agent Service      │     │  Agent Service      │
  │  (FastAPI) Port     │     │  (FastAPI) Port     │
  │  8000 (Replica 1)   │     │  8000 (Replica 2)   │
  │  - REST API         │     │  - REST API         │
  │  - WebSocket        │     │  - WebSocket        │
  │  - Business Logic   │     │  - Business Logic   │
  │  - ORM (SQLAlchemy) │     │  - ORM (SQLAlchemy) │
  └────────────┬────────┘     └────────────┬────────┘
               │                           │
               └────────────┬──────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ PostgreSQL   │   │ Redis        │   │ Prometheus   │
│ Primary DB   │   │ Cache/Queue  │   │ Metrics      │
│ Port 5432    │   │ Port 6379    │   │ Port 9090    │
└──────────────┘   └──────────────┘   └──────────────┘
```

### 1.2 Deployment Scenarios

#### Development (Docker Compose)
- All services in containers on single machine
- Shared Docker network
- Hot reload enabled (except Dockerfiles)
- Demo data pre-seeded
- Used for local development and testing

#### Staging (GitHub Actions)
- Runs full test suite on PR/push
- Builds Docker images with multi-platform support
- Pushes to Docker registry
- Deploys to Kubernetes staging cluster
- Health checks verify deployment

#### Production (Kubernetes)
- Multi-replica deployments with HPA
- Persistent volumes for databases
- Ingress with Let's Encrypt TLS
- Sealed Secrets for sensitive data
- Prometheus + Grafana monitoring
- Sentry error tracking
- Automated backups

---

## 2. Component Deep Dive

### 2.1 Frontend (React + TypeScript)

**Location**: `/frontend`

**Technology Stack**:
- **Framework**: React 18 + TypeScript (strict mode)
- **Build Tool**: Vite
- **State Management**: Zustand with persist middleware
- **Routing**: React Router v6
- **Real-time**: Native WebSocket client
- **Testing**: Vitest + Playwright
- **Styling**: CSS (responsive, mobile-first)
- **Package Manager**: npm 9+

**Key Components**:

```
frontend/src/
├── components/
│   ├── Auth/
│   │   ├── LoginForm.tsx           # JWT login, Bearer token
│   │   └── ProtectedRoute.tsx      # Route guard wrapper
│   ├── Conversations/
│   │   ├── ConversationsPage.tsx   # List + detail view
│   │   ├── MessageList.tsx         # Real-time message display
│   │   ├── MessageInput.tsx        # Message input with validation
│   │   └── MessageItem.tsx         # Individual message rendering
│   ├── Customers/
│   │   ├── CustomersPage.tsx       # List + detail panel
│   │   ├── CustomerModal.tsx       # Create/Update form
│   │   └── CustomerCard.tsx        # Summary display
│   └── Opportunities/
│       ├── OpportunitiesPage.tsx   # List with filters
│       ├── OpportunityModal.tsx    # Create/Update form
│       └── OpportunityCard.tsx     # Stage-based display
├── hooks/
│   ├── useWebSocket.ts             # WebSocket connection management
│   └── useAuth.ts                  # Authentication state
├── stores/
│   ├── authStore.ts                # Auth + user info
│   ├── conversationStore.ts        # Message list + metadata
│   └── crmStore.ts                 # Customers + opportunities
├── services/
│   └── api.ts                      # REST API client
└── utils/
    └── websocket.ts                # WebSocket protocol handler
```

**Data Flow**:

1. **User Login** → JWT stored in localStorage → Auto-restore on refresh
2. **API Requests** → Bearer token in Authorization header
3. **WebSocket Messages** → JWT in initial handshake frame
4. **Optimistic Updates** → Temporary message IDs, status tracking
5. **State Persistence** → Zustand persist middleware saves to localStorage

**Key Features**:

- **WebSocket Integration**: Auto-reconnect with exponential backoff (1s → 32s)
- **Optimistic Updates**: Temporary message IDs, automatic rollback on error
- **Connection Fallback**: Falls back to polling (5s intervals) if WebSocket fails
- **Real-time Sync**: Subscription-based message delivery
- **Error Boundaries**: Graceful degradation for component failures
- **Accessibility**: ARIA labels, keyboard navigation, screen reader support

### 2.2 Gateway (Go)

**Location**: `/backend/go`

**Technology Stack**:
- **Language**: Go 1.21+
- **HTTP Framework**: Standard library + custom router
- **Protocol Support**: HTTP/1.1, WebSocket, HTTP/2
- **Middleware**: CORS, logging, request tracing
- **Performance**: Concurrent request handling, connection pooling

**Responsibilities**:

```go
// main.go structure
1. CORS Validation
   - Reads CORS_ALLOWED_ORIGINS from environment
   - Validates origin on each request
   - Returns 403 Forbidden for unauthorized origins
   - Prevents cross-site WebSocket attacks

2. HTTP Routing
   - POST /login → FastAPI backend
   - GET/POST /conversations/* → FastAPI backend
   - GET/POST /customers/* → FastAPI backend
   - GET/POST /opportunities/* → FastAPI backend
   - GET /health → Local health check

3. WebSocket Proxy
   - Upgrades connection with Origin validation
   - Forwards to FastAPI WebSocket handler
   - Maintains connection state
   - Handles disconnects and errors

4. Logging & Tracing
   - Logs all requests: method, path, status, duration
   - Traces requests with correlation IDs
   - Captures error details for debugging

5. Health Checks
   - Exposes /health endpoint (port 8080)
   - Returns service status
   - Used by Kubernetes liveness probes
```

**Configuration**:

```yaml
Environment Variables:
  CORS_ALLOWED_ORIGINS: "http://localhost:3000,http://localhost:8000"
  GATEWAY_PORT: "8080"
  AGENT_SERVICE_URL: "http://localhost:8000"
```

**Deployment Readiness**:

- ✅ CORS validation implemented
- ✅ Health check endpoint
- ✅ Proper error handling
- ✅ Connection pooling configured
- ✅ No hot-reload in production

### 2.3 Backend / Agent Service (FastAPI + Python)

**Location**: `/backend/python/agent_service`

**Technology Stack**:
- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Task Queue**: Celery 5.3
- **Async**: asyncio + aioredis
- **Validation**: Pydantic v2
- **Testing**: pytest + pytest-asyncio
- **Monitoring**: Prometheus + Sentry

**Architecture**:

```python
agent_service/
├── main.py                    # FastAPI app, routes, middleware
├── models.py                  # SQLAlchemy ORM models (7 models)
├── schemas.py                 # Pydantic request/response schemas
├── database.py                # SQLAlchemy session factory
├── redis_client.py            # Redis connection pool
├── handlers/
│   ├── auth.py               # JWT generation/validation
│   ├── conversations.py       # Conversation CRUD + WebSocket
│   ├── customers.py          # Customer CRUD
│   ├── opportunities.py       # Opportunity CRUD
│   └── messages.py           # Message operations
├── tasks/
│   ├── __init__.py          # Celery app
│   └── async_tasks.py       # Async task definitions
└── seeds.py                  # Demo data seeding
```

**Core Endpoints**:

```python
# Authentication
POST /login
  Request: {"username": str, "password": str}
  Response: {"access_token": str, "token_type": "bearer"}
  Rate Limit: 5/minute

# Conversations
POST /conversations
  Create new conversation
  Rate Limit: 30/minute
  Auth: JWT required

GET /conversations/{conversation_id}
  Fetch single conversation with metadata
  Rate Limit: 60/minute

# Messages
GET /conversations/{conversation_id}/messages
  Paginated message history
  Rate Limit: 60/minute
  Query Params: limit=50, offset=0

POST /messages
  Send message to conversation (optimistic updates)
  Rate Limit: 100/minute
  Payload: {"conversation_id": uuid, "text": str}

# WebSocket
WS /ws
  Real-time message delivery
  Auth: JWT in first frame
  Protocol: JSON message format

# Customers
POST /customers
  Create customer
  Rate Limit: 30/minute

GET /customers/{customer_id}
  Fetch customer details
  Rate Limit: 100/minute

PUT /customers/{customer_id}
  Update customer
  Rate Limit: 30/minute

DELETE /customers/{customer_id}
  Delete customer
  Rate Limit: 30/minute

# Opportunities
POST /opportunities
  Create opportunity
  Rate Limit: 30/minute

GET /opportunities
  List opportunities with filters
  Rate Limit: 60/minute

PUT /opportunities/{opportunity_id}
  Update opportunity

DELETE /opportunities/{opportunity_id}
  Delete opportunity
```

**Database Models**:

```python
# 7 Core Models
1. User
   - id (UUID, PK)
   - username (str, unique)
   - password (str, hashed)
   - email (str, unique)
   - created_at (datetime)
   - updated_at (datetime)

2. Conversation
   - id (UUID, PK)
   - user_id (FK User)
   - title (str)
   - created_at (datetime)
   - updated_at (datetime)

3. Message
   - id (UUID, PK)
   - conversation_id (FK Conversation)
   - user_id (FK User)
   - text (str)
   - created_at (datetime)
   - updated_at (datetime)

4. Customer
   - id (UUID, PK)
   - user_id (FK User)
   - name (str)
   - email (str)
   - phone (str)
   - company (str)
   - status (enum: lead, prospect, customer)
   - created_at (datetime)
   - updated_at (datetime)

5. Opportunity
   - id (UUID, PK)
   - customer_id (FK Customer)
   - user_id (FK User)
   - title (str)
   - amount (decimal)
   - stage (enum: prospecting, qualification, proposal, negotiation, closed_won, closed_lost)
   - probability (int: 0-100)
   - close_date (date)
   - created_at (datetime)
   - updated_at (datetime)

6. Task
   - id (UUID, PK)
   - user_id (FK User)
   - opportunity_id (FK Opportunity)
   - title (str)
   - description (str)
   - status (enum: open, in_progress, completed)
   - due_date (date)
   - created_at (datetime)
   - updated_at (datetime)

7. Agent Response
   - id (UUID, PK)
   - user_id (FK User)
   - query (str)
   - response (str)
   - execution_time_ms (int)
   - created_at (datetime)
```

**Middleware Stack**:

```python
# Order matters for performance
1. CORS middleware
   - Configured in main.py
   - Allows all methods: GET, POST, PUT, DELETE, OPTIONS
   - Headers: Authorization, Content-Type, Accept

2. Request logging
   - Logs method, path, status, duration
   - Structured format: JSON

3. Error handling
   - HTTPException → 4xx responses
   - DatabaseError → 500 with correlation ID
   - ValidationError → 422 with field details
   - RateLimitError → 429 with retry-after

4. Authentication
   - JWT validation on protected routes
   - Token refresh logic (not yet implemented, use stateless tokens)
   - Session tracking via Redis

5. Rate limiting (slowapi)
   - Per-endpoint limits configured
   - Redis backend for distributed rate limiting
   - Returns 429 with retry-after header

6. Prometheus metrics
   - http_requests_total
   - http_request_duration_seconds
   - db_query_duration_seconds
   - agent_responses_total
   - agent_response_time_seconds

7. Sentry error tracking
   - Auto-captures uncaught exceptions
   - Distributed tracing (10% sample rate)
   - Performance monitoring
   - User context tracking
```

**Key Implementation Details**:

- **Async/Await**: All I/O operations are async
- **Connection Pooling**: SQLAlchemy pool_size=20, max_overflow=40
- **Redis Integration**: aioredis for async Redis operations
- **Celery Tasks**: Long-running operations offloaded to worker pool
- **Database Migrations**: Alembic handles schema versioning
- **Health Check Endpoint**: `/health` returns database + Redis status
- **Graceful Shutdown**: SIGTERM handler for clean container termination

### 2.4 Database (PostgreSQL)

**Location**: `schema.sql` + `migrations/` folder

**Schema**:

```sql
-- Core Tables
CREATE TABLE users (
  id UUID PRIMARY KEY,
  username VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conversations (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
  id UUID PRIMARY KEY,
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  text TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customers (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255),
  phone VARCHAR(20),
  company VARCHAR(255),
  status VARCHAR(50) DEFAULT 'lead',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE opportunities (
  id UUID PRIMARY KEY,
  customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  amount DECIMAL(15, 2),
  stage VARCHAR(50) DEFAULT 'prospecting',
  probability INTEGER DEFAULT 0,
  close_date DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(50) DEFAULT 'open',
  due_date DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agent_responses (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  query TEXT NOT NULL,
  response TEXT,
  execution_time_ms INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_customers_user_id ON customers(user_id);
CREATE INDEX idx_opportunities_customer_id ON opportunities(customer_id);
CREATE INDEX idx_opportunities_user_id ON opportunities(user_id);
CREATE INDEX idx_opportunities_stage ON opportunities(stage);
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_opportunity_id ON tasks(opportunity_id);
```

**Migration Strategy**:

- Alembic handles database versioning
- Auto-generated migrations in `migrations/versions/`
- Two-way migrations: `upgrade()` and `downgrade()`
- Applied during container startup via `docker-compose.yml`
- Automatic backup before migrations (production)

**Backup Strategy**:

```bash
# Daily automated backups
./scripts/database-backup.sh

# Backup Location: /backups/touchcli-<timestamp>.sql
# Retention: 30 days
# Frequency: Daily at 02:00 UTC

# Restore from backup
psql touchcli < /backups/touchcli-<timestamp>.sql

# Verify restore
SELECT COUNT(*) FROM users;
```

### 2.5 Redis Cache & Message Broker

**Location**: Docker container or managed service

**Usage Patterns**:

```python
# Session Management
redis.setex(f"session:{user_id}", 3600, json.dumps(session_data))
redis.get(f"session:{user_id}")

# Message Queue (Celery)
celery.send_task('tasks.process_message', args=[message_id])

# Real-time Subscriptions
redis.subscribe('conversation:{conversation_id}')

# Rate Limiting
redis.incr(f"rate_limit:{endpoint}:{client_ip}")
redis.expire(f"rate_limit:{endpoint}:{client_ip}", 60)
```

**Configuration**:

```yaml
Redis Connection:
  Host: localhost (development) / redis.touchcli (k8s)
  Port: 6379
  Database: 0 (sessions), 1 (celery)
  Max Connections: 50
  Timeout: 5s
```

### 2.6 Monitoring Stack

**Prometheus** (Metrics Collection)
- Port: 9090
- Scrape interval: 15 seconds
- Data retention: 30 days
- Service discovery: Kubernetes pod annotations

**Grafana** (Visualization)
- Port: 3001
- Pre-configured Prometheus datasource
- Dashboard templates ready for extension
- Admin account with configurable password

**Sentry** (Error Tracking)
- Automatic error capture
- Distributed tracing (10% sample rate)
- Performance monitoring
- User context tracking
- Release tracking and regressions

**Metrics Collected**:

```
HTTP Layer:
  - http_requests_total (Counter)
  - http_request_duration_seconds (Histogram)
  - http_request_size_bytes (Summary)
  - http_response_size_bytes (Summary)

Database Layer:
  - db_query_duration_seconds (Histogram)
  - db_connection_pool_connections (Gauge)
  - db_connection_pool_overflow (Gauge)

Agent Layer:
  - agent_responses_total (Counter)
  - agent_response_time_seconds (Histogram)
  - agent_errors_total (Counter)

Custom Business Metrics:
  - conversations_created_total (Counter)
  - messages_sent_total (Counter)
  - customers_created_total (Counter)
  - opportunities_created_total (Counter)
```

---

## 3. Technology Decisions & Rationales

### 3.1 Frontend Framework Selection

**Decision**: React 18 + TypeScript (strict mode)

**Rationale**:
- Large ecosystem, extensive component libraries
- Strong type safety with TypeScript
- Excellent developer tooling (Vite, ESLint, Prettier)
- Large hiring pool for maintenance
- Proven production stability
- Server-side rendering not needed (SPA model)

**Alternatives Considered**:
- Vue 3: Similar capabilities, smaller ecosystem
- Svelte: Excellent DX, smaller community
- Angular: Heavier, more opinionated

### 3.2 Backend Framework Selection

**Decision**: FastAPI + SQLAlchemy

**Rationale**:
- Modern async/await support
- Automatic OpenAPI documentation
- Excellent type hints integration
- Fast development velocity
- Strong performance benchmarks
- Large ecosystem of middleware

**Alternatives Considered**:
- Django: More batteries-included, slower for async
- Flask: Too lightweight for this scope
- Node.js: Good but Python favored for data operations

### 3.3 State Management

**Decision**: Zustand (frontend) + Redux-style pattern

**Rationale**:
- Minimal boilerplate vs Redux
- Built-in persist middleware
- Type-safe with TypeScript
- Small bundle size (~2KB)
- Easy testing

**Rationale for API-first backend state**:
- Single source of truth on server
- Easier consistency checking
- Supports multiple clients
- Natural for real-time systems

### 3.4 Real-time Communication

**Decision**: WebSocket via native API

**Rationale**:
- Built-in browser support, no additional libraries
- Lower latency than polling
- Perfect for chat applications
- Bidirectional communication
- Works through most proxies/firewalls

**Alternatives Considered**:
- Socket.IO: Adds abstraction, more overhead
- MQTT: Overkill for single-page app
- Server-Sent Events: Unidirectional only

### 3.5 Containerization & Orchestration

**Decision**: Docker + Kubernetes

**Rationale**:
- Industry standard for deployment
- Easy multi-environment management
- Excellent scaling capabilities
- Cloud-agnostic (AWS, Azure, GCP)
- Strong monitoring ecosystem
- Self-healing with restarts

**Deployment Options**:
- **Development**: Docker Compose
- **Staging**: Kubernetes with auto-scaling
- **Production**: Kubernetes with high availability

### 3.6 Secrets Management

**Decision**: Sealed Secrets (Kubernetes native)

**Rationale**:
- No external secret management needed
- Encrypted at rest in Git
- Per-namespace encryption
- Automatic decryption on pod startup
- Full audit trail

**Workflow**:
1. Developer creates `.env.production` locally (never committed)
2. Runs `./scripts/seal-secrets.sh` to encrypt
3. Encrypted YAML committed to Git (safe)
4. Controller automatically decrypts for pod injection

---

## 4. Data Flow & Integration Patterns

### 4.1 Authentication Flow

```
┌─────────────┐
│ User Login  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│ POST /login                         │
│ - Validate username/password        │
│ - Hash comparison                   │
│ - Generate JWT token (HS256)        │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Browser localStorage                │
│ - Store access_token                │
│ - Store token_type = "bearer"       │
│ - Store user metadata               │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Subsequent Requests                 │
│ - Authorization: Bearer <token>     │
│ - JWT validated on backend          │
│ - User context extracted            │
└─────────────────────────────────────┘
```

### 4.2 Message Flow (WebSocket)

```
┌─────────────┐
│ User Types  │
│ Message     │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Local Optimistic Update              │
│ - Create temp message with ID        │
│ - Mark as "sending"                  │
│ - Display immediately in UI          │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ POST /messages (or WebSocket send)   │
│ - Send actual message text           │
│ - Include conversation_id            │
│ - Include user_id                    │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Backend Processing                   │
│ - Validate user authorization        │
│ - Save to PostgreSQL                 │
│ - Publish to Redis channel           │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ WebSocket Broadcast                  │
│ - Send to all connected clients      │
│ - Include final message ID           │
│ - Include server timestamp           │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Frontend Update                      │
│ - Replace temp ID with server ID     │
│ - Mark as "sent"                     │
│ - Update timestamp                   │
└──────────────────────────────────────┘
```

### 4.3 CRUD Operation Pattern

**Create Example** (Customer):

```
Frontend                          Backend
  │                                 │
  ├─ POST /customers ──────────────>│
  │  {name, email, phone, company}  │
  │                                 │
  │  ✓ Validate input               │
  │  ✓ Check authorization          │
  │                                 │
  │<──────── 201 Created ───────────┤
  │  {id, name, email, ...}         │
  │                                 │
  ├─ Update local state             │
  ├─ Add to Zustand store           │
  ├─ Display success notification   │
  └─ Redirect to detail view        │
```

**Update Example**:

```
Frontend                          Backend
  │                                 │
  ├─ PUT /customers/{id} ────────────>│
  │  {name, email, phone, company}    │
  │                                   │
  │  ✓ Validate user owns resource    │
  │  ✓ Validate input                 │
  │  ✓ Update in database             │
  │                                   │
  │<──────── 200 OK ─────────────────┤
  │  {id, name, email, ...}           │
  │                                   │
  ├─ Update local state              │
  └─ Display success notification    │
```

---

## 5. Deployment Architecture

### 5.1 Development Stack (docker-compose)

```yaml
version: '3.8'

services:
  frontend:
    image: node:18
    volumes:
      - ./frontend:/app
    ports:
      - "3000:5173"  # Vite dev server

  backend:
    image: python:3.11
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/touchcli
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend/python:/app
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  gateway:
    build: ./backend/go
    ports:
      - "8080:8080"
    environment:
      - AGENT_SERVICE_URL=http://backend:8000
    depends_on:
      - backend

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=touchcli
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 5.2 Production Stack (Kubernetes)

**Namespaces**:
- `touchcli` - Application services
- `monitoring` - Prometheus, Grafana, Sentry
- `sealed-secrets` - Secret controller

**Key Manifests**:
- `namespace.yaml` - TouchCLI namespace
- `configmap.yaml` - Non-sensitive config
- `secrets.yaml` - Sealed secrets for credentials
- `frontend-deployment.yaml` - React SPA (3 replicas)
- `backend-deployment.yaml` - FastAPI (2 replicas)
- `gateway-deployment.yaml` - Go proxy (2 replicas)
- `ingress.yaml` - HTTPS entry point
- `prometheus-config.yaml` - Metrics collection
- `grafana-config.yaml` - Dashboards
- `sealed-secrets-controller.yaml` - Secret encryption

**High Availability Features**:
- Multi-replica deployments
- Health checks (liveness + readiness)
- Pod disruption budgets
- Auto-scaling based on metrics
- Rolling updates with zero downtime
- Persistent volumes for databases
- Automatic failover

---

## 6. Security Architecture

### 6.1 Authentication & Authorization

**JWT Tokens**:
- Algorithm: HS256
- Payload: `{sub: user_id, iat: issued_at, exp: expiration}`
- Expiration: 24 hours
- Stored in: Browser localStorage
- Transmitted via: Authorization: Bearer header

**Authorization Levels**:
- Anonymous: Can access login page
- Authenticated: Can access all API endpoints for their own data
- Data isolation: Users cannot access other users' data via API

**CORS Configuration**:

```python
# Gateway validates origins
CORS_ALLOWED_ORIGINS = [
  "http://localhost:3000",
  "http://localhost:8000",
  "https://touchcli.example.com",
]

# Rejects: cross-origin WebSocket attacks
# Allows: legitimate AJAX from configured origins
```

### 6.2 Data Protection

**In Transit**:
- HTTPS/TLS 1.3 (production)
- HTTP/2 for performance
- WebSocket Secure (WSS) for real-time
- Let's Encrypt certificates (auto-renew)

**At Rest**:
- PostgreSQL: Encryption at storage layer (cloud provider responsibility)
- Redis: In-memory, no persistent data except sessions
- Secrets: Sealed Secrets encrypted with RSA-4096

**Password Security**:
- Bcrypt hashing with salt (workfactor=12)
- Never stored in logs
- Never transmitted in URL/cookie

### 6.3 API Security

**Input Validation**:
- Pydantic schemas validate all inputs
- Type checking enforced
- SQL injection prevention via parameterized queries
- XSS prevention via JSON encoding

**Rate Limiting**:
- Per-endpoint limits via slowapi
- Login: 5/minute (prevent brute force)
- Create operations: 30/minute
- Read operations: 100/minute
- Returns: 429 Too Many Requests with Retry-After header

**Error Handling**:
- Sensitive errors never exposed to client
- Correlation IDs for debugging
- Sentry captures for monitoring
- Graceful degradation (no data leaks)

### 6.4 Container Security

**Non-root Users**:
```dockerfile
# Dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

**Image Scanning**:
- Trivy scans for vulnerabilities
- Snyk monitors dependencies
- Regular updates scheduled

**Resource Limits**:
```yaml
# Kubernetes
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

---

## 7. Performance Optimization

### 7.1 Frontend Performance

**Bundle Size Optimization**:
- Code splitting by route (React.lazy)
- Tree shaking with Vite
- Gzip compression (nginx)
- Asset hashing for caching

**Runtime Performance**:
- Memoization for expensive components
- Zustand state selectors to prevent re-renders
- Virtual scrolling for long lists
- Debounced search inputs

**Network Performance**:
- WebSocket for real-time (vs polling)
- Service worker for offline support (ready)
- Lazy loading images
- API response caching

### 7.2 Backend Performance

**Database Optimization**:
- Connection pooling (min=5, max=20)
- Query result caching via Redis
- Strategic indexes on foreign keys and frequently filtered columns
- EXPLAIN ANALYZE used for query optimization

**API Response Optimization**:
- Pagination for list endpoints
- Field selection (limit what's returned)
- Compressed responses (gzip)
- HTTP caching headers

**Async Processing**:
- I/O operations are async
- Long-running tasks offloaded to Celery
- WebSocket broadcast avoids blocking
- Connection timeouts (5 seconds)

### 7.3 Benchmarks

**Target SLAs**:
- API response: <500ms p95
- WebSocket latency: <100ms RTT
- Database query: <50ms p95
- Frontend load: <3s on 4G

**Monitoring**:
- Prometheus metrics tracked continuously
- Grafana dashboards visible to team
- Alerts fired if SLAs violated
- Performance regression detected in CI

---

## 8. Operational Concerns

### 8.1 Scalability Strategy

**Horizontal Scaling**:
- Kubernetes HPA scales pods based on CPU/memory
- Stateless services (no session affinity needed)
- Database connection pooling handles multiple apps
- Redis pub/sub for inter-process communication

**Vertical Scaling**:
- Database replication for read scaling
- Read replicas for reporting
- Cache warming for hot data

### 8.2 Disaster Recovery

**RTO/RPO Targets**:
- Recovery Time Objective: 1 hour
- Recovery Point Objective: 5 minutes (backup frequency)

**Backup Strategy**:
- Daily automated database backups
- 30-day retention
- Offsite storage (S3/GCS)
- Weekly restore testing

**Failover Strategy**:
- Kubernetes handles pod failures automatically
- Database replication provides failover
- DNS failover (multiple ingress IPs)
- Health checks trigger automatic restart

### 8.3 Monitoring & Observability

**Metrics**:
- Prometheus collects 15+ metrics
- Grafana dashboards for visualization
- Sentry tracks errors in real-time
- CloudWatch (AWS) for infrastructure

**Logging**:
- Structured JSON logging
- Centralized log aggregation (ELK ready)
- Log retention: 30 days
- Correlation IDs for request tracing

**Alerting**:
- PagerDuty integration for critical alerts
- Slack notifications for warnings
- Email digest of daily summaries
- On-call escalation path defined

---

## 9. Known Limitations & Future Enhancements

### 9.1 Current Limitations

1. **Single-region deployment**: No cross-region replication
2. **No audit logging**: Who changed what, when not tracked
3. **Basic authentication**: No OAuth/SAML yet
4. **No search**: Cannot search conversations/messages
5. **No bulk operations**: Cannot export/bulk update
6. **No offline mode**: Requires active internet

### 9.2 Planned Enhancements

**Phase 4 (Optional)**:
1. Advanced search with full-text indexing
2. Export to PDF/Excel
3. Email notifications
4. Calendar integration
5. Mobile app
6. Audit logging
7. Role-based access control
8. Multi-tenant support

**Long-term**:
1. AI-powered insights and recommendations
2. Voice input/output
3. Integration with external CRMs
4. Advanced reporting and analytics
5. Global scaling with CDN

---

## 10. Technology Matrix

| Component | Technology | Version | Status |
|-----------|-----------|---------|--------|
| **Frontend** | React | 18+ | ✅ Production |
| | TypeScript | 5.x | ✅ Production |
| | Vite | 4.x | ✅ Production |
| | Zustand | 4.x | ✅ Production |
| **Backend** | FastAPI | 0.104+ | ✅ Production |
| | Python | 3.11+ | ✅ Production |
| | SQLAlchemy | 2.0+ | ✅ Production |
| | Celery | 5.3+ | ✅ Production |
| **Gateway** | Go | 1.21+ | ✅ Production |
| | Standard lib | Built-in | ✅ Production |
| **Database** | PostgreSQL | 15+ | ✅ Production |
| | Redis | 7+ | ✅ Production |
| **Infrastructure** | Docker | 24+ | ✅ Production |
| | Kubernetes | 1.26+ | ✅ Production |
| | GitHub Actions | Latest | ✅ Production |
| **Monitoring** | Prometheus | 2.40+ | ✅ Production |
| | Grafana | 9+ | ✅ Production |
| | Sentry | Latest | ✅ Production |

---

## 11. Communication Protocols

### 11.1 REST API

**Base URL**: `http://localhost:8080/api`

**Request Format**:
```http
POST /conversations
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "title": "Q1 Planning"
}
```

**Response Format**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "title": "Q1 Planning",
  "created_at": "2026-03-02T10:30:00Z",
  "updated_at": "2026-03-02T10:30:00Z"
}
```

**Error Format**:
```json
{
  "detail": "Conversation not found",
  "status": 404,
  "type": "Not Found"
}
```

### 11.2 WebSocket Protocol

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

// Authentication in first frame
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: "auth",
    token: "Bearer eyJhbGc..."
  }));
};
```

**Message Format**:
```json
{
  "type": "message",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "text": "Hello world",
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "timestamp": "2026-03-02T10:30:00Z"
}
```

**Heartbeat**:
```json
{
  "type": "ping"
}
```

---

## Conclusion

TouchCLI is a **modern, production-ready system** built with industry best practices:

- ✅ Type-safe (TypeScript + Pydantic)
- ✅ Secure (JWT + HTTPS + sealed secrets)
- ✅ Scalable (Kubernetes + auto-scaling)
- ✅ Observable (Prometheus + Grafana + Sentry)
- ✅ Testable (176+ tests)
- ✅ Well-documented (This architecture doc + code comments)
- ✅ Ready for production deployment

For operational procedures, see **OPERATIONS_GUIDE.md**.
For troubleshooting, see **TROUBLESHOOTING.md**.
For incident response, see **RUNBOOKS.md**.
