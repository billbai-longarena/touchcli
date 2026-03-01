# Phase 2: Backend Infrastructure Implementation Plan

> **Status**: 🔴 IN PROGRESS (Worker phase, S-003 claimed)
> **Timeline**: 4-5 weeks
> **Signal**: S-003 (w:51 HOLE)
> **Caste**: Worker
> **Worker ID**: termite-1772386406-56018
> **Foundation**: Phase 1 specs complete (schema.sql, openapi.yaml, WEBSOCKET_SPEC.md, REDIS_SCHEMA.md)

---

## Overview

Phase 2 implements the live backend system based on Phase 1 specifications. It bridges the gap between design docs and running services.

## Architecture Decision

**Language**: Python (FastAPI) + Go (Gateway) hybrid approach
- **Python (FastAPI)**: Agent logic, business logic, easier LangGraph integration
- **Go (Gin)**: Gateway, high-throughput HTTP routing, WebSocket management

**Rationale**:
- LangGraph (Python) is the primary Agent framework
- Go provides better concurrency for WebSocket connections
- Separation of concerns: compute (Python) vs. networking (Go)

---

## Task Breakdown

### Task 2.1: Project Structure & Dependency Setup

**Objective**: Create scaffolding and dependency management.

**Subtasks**:
- [ ] Create `backend/` directory structure
  ```
  backend/
  ├── python/
  │   ├── agent_service/
  │   │   ├── __init__.py
  │   │   ├── main.py (FastAPI app)
  │   │   ├── router.py (Agent Router)
  │   │   ├── agents/ (Sales, Data, Strategy, etc.)
  │   │   ├── tools/ (database, api, memory)
  │   │   ├── models.py (Pydantic models)
  │   │   ├── db.py (SQLAlchemy ORM)
  │   │   └── config.py (settings)
  │   ├── requirements.txt (deps)
  │   ├── pyproject.toml (poetry or pip-tools)
  │   └── tests/
  ├── go/
  │   ├── gateway/
  │   │   ├── main.go
  │   │   ├── websocket.go
  │   │   ├── http_proxy.go
  │   │   └── config/
  │   ├── go.mod
  │   └── go.sum
  ├── migrations/ (Alembic for Python ORM)
  └── docker-compose.yml (local development)
  ```

- [ ] Python dependencies
  ```
  fastapi==0.104.1
  uvicorn==0.24.0
  sqlalchemy==2.0.23
  psycopg2-binary==2.9.9
  redis==5.0.1
  langgraph==0.0.1+ (latest)
  pydantic==2.5.0
  python-dotenv==1.0.0
  alembic==1.13.0
  ```

- [ ] Go dependencies
  ```
  go get github.com/gin-gonic/gin
  go get github.com/gorilla/websocket
  go get github.com/joho/godotenv
  go get github.com/go-redis/redis/v8
  ```

- [ ] Environment configuration (`.env.example`)
  ```
  # Database
  DATABASE_URL=postgresql://user:password@localhost:5432/touchcli
  REDIS_URL=redis://localhost:6379/0

  # LangGraph
  LANGGRAPH_API_KEY=xxx

  # Server
  AGENT_SERVICE_PORT=8000
  GATEWAY_PORT=8080

  # Logging
  LOG_LEVEL=INFO
  ```

**Deliverables**:
- Directory structure created
- requirements.txt + pyproject.toml
- go.mod + go.sum
- docker-compose.yml for local dev (PostgreSQL + Redis + Python service + Go gateway)

---

### Task 2.2: Database Layer (SQLAlchemy ORM)

**Objective**: Map Phase 1 schema.sql to Python ORM models.

**Subtasks**:
- [ ] Create Pydantic models (`models.py`)
  ```python
  class UserCreate(BaseModel):
      email: str
      name: str
      role: str = "salesperson"

  class ConversationCreate(BaseModel):
      customer_id: Optional[UUID]
      opportunity_id: Optional[UUID]

  class MessageCreate(BaseModel):
      conversation_id: UUID
      content: str
      attachments: List[dict] = []
  ```

- [ ] Create SQLAlchemy models (`db/models.py`)
  ```python
  class User(Base):
      __tablename__ = "users"
      id = Column(UUID, primary_key=True, default=uuid4)
      email = Column(String, unique=True)
      name = Column(String)
      # ... mapped from schema.sql

  class Conversation(Base):
      __tablename__ = "conversations"
      id = Column(UUID, primary_key=True)
      user_id = Column(UUID, ForeignKey("users.id"))
      # ...
  ```

- [ ] Database connection & session management (`db.py`)
  ```python
  DATABASE_URL = os.getenv("DATABASE_URL")
  engine = create_engine(DATABASE_URL, pool_pre_ping=True)
  SessionLocal = sessionmaker(bind=engine)

  def get_db():
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
  ```

- [ ] Alembic migrations
  ```bash
  alembic init migrations
  alembic revision --autogenerate -m "initial schema from Phase 1"
  alembic upgrade head
  ```

**Deliverables**:
- `backend/python/agent_service/models.py` (SQLAlchemy)
- `backend/python/agent_service/schemas.py` (Pydantic)
- `backend/python/agent_service/db.py` (session management)
- `migrations/` directory with initial migration
- ORM models tested with Phase 1 schema

---

### Task 2.3: FastAPI Server Foundation

**Objective**: Build the Agent service REST API.

**Subtasks**:
- [ ] FastAPI app initialization (`main.py`)
  ```python
  from fastapi import FastAPI, Depends
  from fastapi.middleware.cors import CORSMiddleware

  app = FastAPI(
      title="TouchCLI Agent Service",
      version="1.0.0"
  )

  # CORS
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"]
  )
  ```

- [ ] Implement API endpoints (from openapi.yaml)
  ```python
  @app.post("/conversations", response_model=ConversationResponse)
  async def create_conversation(req: ConversationCreate, db: Session = Depends(get_db)):
      # ...

  @app.post("/messages", status_code=202)
  async def send_message(req: MessageCreate, db: Session = Depends(get_db)):
      # Trigger async Agent processing
      # Return task_id for polling
  ```

- [ ] Health check endpoint
  ```python
  @app.get("/health")
  async def health_check(db: Session = Depends(get_db)):
      try:
          db.execute("SELECT 1")
          db_ok = True
      except:
          db_ok = False

      redis_ok = redis_client.ping()

      return {
          "status": "ok" if db_ok and redis_ok else "degraded",
          "database": "ok" if db_ok else "error",
          "cache": "ok" if redis_ok else "error"
      }
  ```

- [ ] Error handling middleware
  ```python
  @app.exception_handler(HTTPException)
  async def http_exception_handler(request, exc):
      return JSONResponse(
          status_code=exc.status_code,
          content={"error": exc.detail, "code": "HTTP_ERROR"}
      )
  ```

**Deliverables**:
- `main.py` — FastAPI app with all /api/v1 endpoints
- Error handling + CORS middleware
- Health check endpoint
- All endpoints tested with sample requests

---

### Task 2.4: WebSocket Server (Go Gateway)

**Objective**: Implement real-time WebSocket server.

**Subtasks**:
- [ ] WebSocket handler (`websocket.go`)
  ```go
  func HandleWebSocket(c *gin.Context) {
      ws, err := upgrader.Upgrade(c.Writer, c.Request, nil)
      if err != nil {
          return
      }
      defer ws.Close()

      client := &Client{
          ID:   uuid.New().String(),
          Conn: ws,
          Send: make(chan []byte, 256),
      }

      hub.Register <- client

      go client.readPump()
      go client.writePump()
  }
  ```

- [ ] Frame parsing (from WEBSOCKET_SPEC.md)
  ```go
  type Frame struct {
      Type           string    `json:"type"` // message, agent-action, etc.
      ID             string    `json:"id"`
      ConversationID string    `json:"conversation_id"`
      Timestamp      time.Time `json:"timestamp"`
      Payload        json.RawMessage `json:"payload"`
  }

  func (c *Client) readPump() {
      for {
          var frame Frame
          err := c.Conn.ReadJSON(&frame)
          if err != nil {
              // Handle error
              break
          }
          // Process frame, forward to Python service
      }
  }
  ```

- [ ] Heartbeat mechanism (30s interval)
  ```go
  ticker := time.NewTicker(30 * time.Second)
  defer ticker.Stop()

  for {
      select {
      case <-ticker.C:
          heartbeat := Frame{
              Type:      "heartbeat",
              ID:        uuid.New().String(),
              Timestamp: time.Now(),
              Payload:   json.RawMessage(`{"status":"ok"}`),
          }
          client.Send <- marshalFrame(heartbeat)
      }
  }
  ```

- [ ] HTTP proxy to FastAPI
  ```go
  @app.POST("/api/v1/*path")
  func ProxyRequest(c *gin.Context) {
      // Forward HTTP requests to Python service
      resp, err := http.Post(
          fmt.Sprintf("http://localhost:8000%s", c.Request.URL.Path),
          "application/json",
          c.Request.Body,
      )
      // Return response
  }
  ```

**Deliverables**:
- `websocket.go` — connection handling
- `hub.go` — client registry & broadcast
- `main.go` — Gin server + WebSocket endpoint + HTTP proxy
- WebSocket tested with sample clients

---

### Task 2.5: Agent Service (LangGraph Integration)

**Objective**: Implement the Agent Router and subagents.

**Subtasks**:
- [ ] LangGraph Router setup (`router.py`)
  ```python
  from langgraph.graph import StateGraph, END

  class ConversationState(TypedDict):
      conversation_id: UUID
      user_message: str
      agent_actions: List[dict]
      memory: dict
      next_agent: str

  workflow = StateGraph(ConversationState)

  def route_agent(state: ConversationState) -> str:
      # Determine next agent based on user_message
      if "deal" in state["user_message"]:
          return "sales"
      elif "data" in state["user_message"]:
          return "data"
      else:
          return "strategy"

  workflow.add_node("router", route_agent)
  ```

- [ ] Sales Agent implementation (`agents/sales_agent.py`)
  ```python
  class SalesAgent:
      def run(self, state: ConversationState):
          # Query opportunities
          opportunities = self.query_opportunities(...)

          # Generate recommendation
          recommendation = self.llm_analyze(opportunities)

          # Update memory
          state["memory"]["sales_context"] = {...}

          return state
  ```

- [ ] Data Agent implementation
- [ ] Strategy Agent implementation
- [ ] Tool definitions (database queries, API calls, memory ops)

**Deliverables**:
- `router.py` — LangGraph Router
- `agents/sales_agent.py`, `agents/data_agent.py`, `agents/strategy_agent.py`
- `tools/` — database, api, memory operation tools
- Agent integration tested end-to-end

---

### Task 2.6: Async Task Queue (BullMQ or Celery)

**Objective**: Handle long-running Agent operations asynchronously.

**Subtasks**:
- [ ] Task queue setup (using Celery + Redis)
  ```python
  from celery import Celery

  celery_app = Celery(
      "touchcli",
      broker=os.getenv("REDIS_URL"),
      backend=os.getenv("REDIS_URL")
  )

  @celery_app.task
  def process_message(message_id: str, content: str):
      # Run Agent workflow
      result = agent_workflow.run(content)
      # Store result
      return result
  ```

- [ ] FastAPI integration
  ```python
  @app.post("/messages")
  async def send_message(req: MessageCreate):
      task = process_message.delay(str(req.conversation_id), req.content)
      return {"task_id": task.id, "message": "Processing..."}

  @app.get("/tasks/{task_id}")
  async def get_task_status(task_id: str):
      task = celery_app.AsyncResult(task_id)
      return {"status": task.status, "result": task.result}
  ```

**Deliverables**:
- `agent_service/tasks.py` — Celery task definitions
- Task monitoring endpoint
- Task status polling example

---

### Task 2.7: Docker & Deployment

**Objective**: Containerize services for local development and cloud deployment.

**Subtasks**:
- [ ] Python service Dockerfile
  ```dockerfile
  FROM python:3.11-slim

  WORKDIR /app
  COPY backend/python/requirements.txt .
  RUN pip install -r requirements.txt

  COPY backend/python/ .

  CMD ["uvicorn", "agent_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

- [ ] Go gateway Dockerfile
  ```dockerfile
  FROM golang:1.21-alpine as builder
  WORKDIR /app
  COPY backend/go .
  RUN go build -o gateway main.go

  FROM alpine:latest
  COPY --from=builder /app/gateway .
  CMD ["./gateway"]
  ```

- [ ] docker-compose.yml (local development)
  ```yaml
  version: '3.8'
  services:
    postgres:
      image: postgres:15
      environment:
        POSTGRES_PASSWORD: password
        POSTGRES_DB: touchcli
      ports:
        - "5432:5432"

    redis:
      image: redis:7
      ports:
        - "6379:6379"

    agent-service:
      build: ./backend/python
      ports:
        - "8000:8000"
      depends_on:
        - postgres
        - redis
      environment:
        DATABASE_URL: postgresql://postgres:password@postgres:5432/touchcli
        REDIS_URL: redis://redis:6379/0

    gateway:
      build: ./backend/go
      ports:
        - "8080:8080"
      depends_on:
        - agent-service
  ```

- [ ] Kubernetes manifests (optional for Phase 2)
  ```yaml
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: agent-service
  spec:
    replicas: 3
    selector:
      matchLabels:
        app: agent-service
    template:
      metadata:
        labels:
          app: agent-service
      spec:
        containers:
        - name: agent-service
          image: touchcli/agent-service:latest
          ports:
          - containerPort: 8000
  ```

**Deliverables**:
- `Dockerfile` (Python service)
- `Dockerfile.gateway` (Go service)
- `docker-compose.yml` (local dev)
- `kubernetes/` manifests (optional)
- Services run in Docker with data persistence

---

## Acceptance Criteria

### Functional
- [ ] All Phase 1 REST API endpoints callable with correct status codes
- [ ] WebSocket connections stable for 5+ minute heartbeat cycles
- [ ] Agent Router correctly dispatches to subagents
- [ ] Database migrations run without errors
- [ ] Redis caching reduces DB query load by > 50%

### Technical
- [ ] Code follows PEP 8 (Python) and Go conventions
- [ ] Logging captures all errors & warnings
- [ ] Error handling prevents service crashes
- [ ] All endpoints tested with integration tests

### Operational
- [ ] Services run via docker-compose
- [ ] Health check endpoint returns correct status
- [ ] Graceful shutdown (no data loss)
- [ ] Monitoring ready (metrics exportable)

---

## Dependencies

- **Depends on**: S-002 Phase 1 Foundation (COMPLETE ✓)
- **Blocks**: S-004 Frontend Integration, S-005 Optimization

## Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| LangGraph API changes | Pin version, monitor releases |
| Database migration failures | Test migrations in CI/CD first |
| WebSocket connection loss | Implement client-side reconnect logic |
| Agent timeout | Set configurable timeouts, implement retry |

---

## Testing Strategy

1. **Unit Tests**: Each agent, tool, endpoint
2. **Integration Tests**: Full workflow (user message → agent → DB → response)
3. **Load Tests**: 100+ concurrent WebSocket connections
4. **Docker Tests**: Services start, communicate, persist data

---

**Status**: Phase 2 In-Progress (Worker phase S-003)
**Last Updated**: 2026-03-02
**Next Session**: Continue with Task 2.1 or delegate to Worker cohort

