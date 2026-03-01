"""
TouchCLI Agent Service - FastAPI Backend
Phase 2: Backend Infrastructure Implementation
"""

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import desc
import os
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from prometheus_client import Counter, Histogram, make_wsgi_app
from prometheus_client import CollectorRegistry, generate_latest

# Import from local modules (use relative imports for package)
try:
    # When running as module
    from .db import get_db, engine, init_db, get_db_health
    from .models import (
        Base, User, Customer, Opportunity, Conversation, Message, AgentState, ActivityLog
    )
    from .schemas import (
        ConversationCreate, ConversationResponse, MessageCreate, MessageResponse,
        CustomerCreate, CustomerResponse, OpportunityCreate, OpportunityResponse,
        HealthCheckResponse, ComponentHealth
    )
    from .workflow import ConversationWorkflow
    from .auth import get_current_user, create_token
except ImportError:
    # Fallback for direct execution
    from db import get_db, engine, init_db, get_db_health
    from models import (
        Base, User, Customer, Opportunity, Conversation, Message, AgentState, ActivityLog
    )
    from schemas import (
        ConversationCreate, ConversationResponse, MessageCreate, MessageResponse,
        CustomerCreate, CustomerResponse, OpportunityCreate, OpportunityResponse,
        HealthCheckResponse, ComponentHealth
    )
    from workflow import ConversationWorkflow
    from auth import get_current_user, create_token

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


def _parse_cors_origins() -> List[str]:
    """Parse CORS origin allowlist from env with safe dev defaults."""
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if raw.strip():
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


SUPPORTED_LOCALES = {"en-US", "zh-CN"}
LOCALE_LANGUAGE_DEFAULTS = {
    "en": "en-US",
    "zh": "zh-CN",
}


def _normalize_locale(raw: Optional[str]) -> Optional[str]:
    """Normalize locale input into xx-YY and limit to supported locales."""
    if not raw:
        return None

    value = raw.strip()
    if not value:
        return None

    # Accept-Language can include comma-separated candidates with q-values.
    value = value.split(",")[0].strip()
    value = value.split(";")[0].strip()
    value = value.replace("_", "-")

    parts = value.split("-")
    if len(parts) == 1:
        return LOCALE_LANGUAGE_DEFAULTS.get(parts[0].lower())

    normalized = f"{parts[0].lower()}-{parts[1].upper()}"
    if normalized in SUPPORTED_LOCALES:
        return normalized
    return None


def _resolve_locale(
    request_locale: Optional[str],
    accept_language: Optional[str],
    preferred_locale: Optional[str],
) -> str:
    """Resolve locale by priority: request body > Accept-Language > user pref > default."""
    for candidate in (request_locale, accept_language, preferred_locale, "en-US"):
        normalized = _normalize_locale(candidate)
        if normalized:
            return normalized
    return "en-US"


app = FastAPI(
    title="TouchCLI Agent Service",
    version="1.0.0",
    description="Conversational Sales Assistant Backend"
)

# ============================================================================
# Observability: Sentry Error Tracking
# ============================================================================
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        environment=os.getenv("ENVIRONMENT", "development"),
        release=os.getenv("APP_VERSION", "1.0.0"),
        debug=os.getenv("DEBUG", "false").lower() == "true"
    )
    logger.info("Sentry error tracking initialized")

# ============================================================================
# Observability: Prometheus Metrics
# ============================================================================
# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0)
)

# Database metrics
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query latency',
    ['operation'],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0)
)

# Agent metrics
agent_responses_total = Counter(
    'agent_responses_total',
    'Total agent responses',
    ['status', 'confidence_level']
)

agent_response_time_seconds = Histogram(
    'agent_response_time_seconds',
    'Agent response processing time',
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
)

logger.info("Prometheus metrics initialized")

# Rate Limiting Configuration
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=429,
    content={"detail": "Rate limit exceeded"}
))
app.add_middleware(SlowAPIMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Configuration
# ============================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/touchcli")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ============================================================================
# Authentication
# ============================================================================

@app.post("/login")
@limiter.limit("5/minute")
async def login(request, user_id: UUID, db: Session = Depends(get_db)):
    """
    Generate JWT token for a user.

    Args:
        user_id: User UUID (in production, would be authenticated via password)

    Returns:
        - access_token: JWT token for subsequent requests
        - token_type: "bearer"
        - user_id: User UUID
    """
    # TODO: In production, verify user credentials (password, MFA, etc.)
    # For now, we accept any user_id and verify they exist in the database

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = create_token(user.id)
    logger.info(f"Generated token for user {user.id}")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(user.id)
    }

# ============================================================================
# Metrics Endpoint (for Prometheus scraping)
# ============================================================================

@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns:
        Prometheus-formatted metrics (text/plain)
    """
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4"
    )

# ============================================================================
# Health Check
# ============================================================================

@app.get("/health", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for load balancers and orchestration.

    Returns:
        - status: "ok", "degraded", or "unhealthy"
        - version, timestamp
        - checks: database, agent_service, cache status
    """
    import time
    import redis as redis_client

    # Check database connectivity
    db_status = "ok"
    db_latency = 0
    db_error = None
    try:
        start = time.time()
        db.execute("SELECT 1")
        db_latency = int((time.time() - start) * 1000)
    except Exception as e:
        db_status = "error"
        db_error = str(e)
        logger.error(f"Database health check failed: {e}")

    # Check Redis connectivity
    redis_ok = True
    redis_latency = 0
    redis_error = None
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        # Extract Redis connection parameters from URL
        redis_connection = redis_client.from_url(redis_url, decode_responses=True)

        start = time.time()
        redis_connection.ping()
        redis_latency = int((time.time() - start) * 1000)
        redis_connection.close()
    except Exception as e:
        redis_ok = False
        redis_error = str(e)
        logger.warning(f"Redis health check failed: {e} (Redis may be unavailable)")

    # Determine overall status
    overall_status = "ok"
    if db_status == "error" or (not redis_ok):
        overall_status = "unhealthy"

    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        checks={
            "database": ComponentHealth(
                status=db_status,
                latency_ms=db_latency,
                last_checked=datetime.utcnow()
            ),
            "agent_service": ComponentHealth(
                status="ok",
                latency_ms=0,
                last_checked=datetime.utcnow()
            ),
            "cache": ComponentHealth(
                status="ok" if redis_ok else "error",
                latency_ms=redis_latency if redis_ok else None,
                last_checked=datetime.utcnow()
            )
        }
    )

# ============================================================================
# Conversation Endpoints
# ============================================================================

@app.post("/conversations", response_model=ConversationResponse, status_code=201)
@limiter.limit("30/minute")
async def create_conversation(request,
    req: ConversationCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
    accept_language: Optional[str] = Header(default=None, alias="Accept-Language"),
):
    """
    Start a new conversation.

    Args:
        customer_id: Optional customer UUID for context
        opportunity_id: Optional opportunity UUID for context

    Returns:
        Conversation object with metadata
    """

    current_user = db.query(User).filter(User.id == user_id).first()
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized user")

    resolved_locale = _resolve_locale(
        request_locale=req.locale,
        accept_language=accept_language,
        preferred_locale=current_user.preferred_locale,
    )

    # Persist latest locale preference from explicit request/header.
    if (req.locale or accept_language) and current_user.preferred_locale != resolved_locale:
        current_user.preferred_locale = resolved_locale
        db.add(current_user)

    # Validate customer_id and opportunity_id if provided
    if req.customer_id:
        customer = db.query(Customer).filter(Customer.id == req.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

    if req.opportunity_id:
        opportunity = db.query(Opportunity).filter(Opportunity.id == req.opportunity_id).first()
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")

    # Create conversation
    conversation = Conversation(
        user_id=user_id,
        customer_id=req.customer_id,
        opportunity_id=req.opportunity_id,
        mode=req.mode,
        locale=resolved_locale,
        metadata_json={"locale": resolved_locale},
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    logger.info(f"Created conversation {conversation.id} for user {user_id}")
    return conversation


@app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
@limiter.limit("60/minute")
async def get_conversation(
    request,
    conversation_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Fetch conversation metadata.

    Args:
        conversation_id: Conversation UUID

    Returns:
        Conversation object with metadata
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation

# ============================================================================
# Message Endpoints
# ============================================================================

@app.post("/messages", status_code=202)
@limiter.limit("100/minute")
async def send_message(
    request,
    req: MessageCreate,
    db: Session = Depends(get_db),
    sender_id: UUID = Depends(get_current_user)
):
    """
    Send message and trigger Agent processing.

    Args:
        conversation_id: Conversation UUID
        content: Message text or voice transcript
        attachments: Optional file/image attachments

    Returns:
        - message_id: New message UUID
        - task_id: Async task ID for polling progress
        - agent_response: Initial agent response
    """
    # Validate conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Create message record
    message = Message(
        conversation_id=req.conversation_id,
        sender_id=sender_id,
        sender_role="user",
        content=req.content,
        content_type=req.content_type,
        attachments=req.attachments or []
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    logger.info(f"Created message {message.id} in conversation {req.conversation_id}")

    # Process through agent workflow
    try:
        workflow = ConversationWorkflow(db)
        result = await workflow.process_message(
            conversation_id=req.conversation_id,
            user_id=conversation.user_id,
            message=req.content,
            customer_id=conversation.customer_id,
            opportunity_id=conversation.opportunity_id,
        )

        # Create agent response message
        agent_message = Message(
            conversation_id=req.conversation_id,
            sender_role="agent",
            content=result.get("agent_response", ""),
            content_type="text",
            attachments=[]
        )
        db.add(agent_message)
        db.commit()

        return {
            "message_id": str(message.id),
            "task_id": str(message.id),  # Use message ID as task ID for now
            "status": "completed",
            "agent_response": result.get("agent_response"),
            "next_agent": result.get("next_agent"),
            "confidence": result.get("confidence"),
        }

    except Exception as e:
        logger.error(f"Agent processing failed: {e}")
        return {
            "message_id": str(message.id),
            "task_id": str(message.id),
            "status": "failed",
            "error": str(e),
            "agent_response": "I encountered an error processing your message. Please try again.",
        }


@app.get("/conversations/{conversation_id}/messages")
@limiter.limit("60/minute")
async def get_messages(
    request,
    conversation_id: UUID,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Fetch conversation message history.

    Args:
        conversation_id: Conversation UUID
        limit: Max messages to return (default 50, max 500)
        offset: Pagination offset

    Returns:
        - messages: List of Message objects
        - total: Total message count
        - limit, offset: Pagination info
    """
    # Validate conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get total count
    total = db.query(Message).filter(Message.conversation_id == conversation_id).count()

    # Fetch messages with pagination
    limit = min(limit, 500)  # Cap at 500
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(desc(Message.created_at)).offset(offset).limit(limit).all()

    return {
        "messages": [MessageResponse.model_validate(m, from_attributes=True) for m in messages],
        "total": total,
        "offset": offset,
        "limit": limit
    }

# ============================================================================
# Opportunity Endpoints
# ============================================================================

@app.post("/opportunities", response_model=OpportunityResponse, status_code=201)
@limiter.limit("30/minute")
async def create_opportunity(
    request,
    req: OpportunityCreate,
    db: Session = Depends(get_db)
):
    """
    Create or update opportunity.

    Args:
        customer_id: Customer UUID (required)
        name: Opportunity name (required)
        amount: Deal amount (required)
        status: sales stage (discovery, proposal, etc.)
        expected_close_date: ISO 8601 format

    Returns:
        Created opportunity object
    """
    # Validate customer exists
    customer = db.query(Customer).filter(Customer.id == req.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Create opportunity
    opportunity = Opportunity(
        customer_id=req.customer_id,
        name=req.name,
        description=req.description,
        amount=req.amount,
        currency=req.currency,
        status=req.status,
        probability=req.probability,
        expected_close_date=req.expected_close_date,
        metadata_json=req.metadata
    )
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)

    logger.info(f"Created opportunity {opportunity.id} for customer {req.customer_id}")
    return opportunity


@app.get("/opportunities")
@limiter.limit("60/minute")
async def list_opportunities(
    request,
    status: Optional[str] = None,
    customer_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Query opportunities with filters.

    Args:
        status: Filter by sales stage
        customer_id: Filter by customer
        limit, offset: Pagination

    Returns:
        - opportunities: List of Opportunity objects
        - total: Total matching count
    """
    query = db.query(Opportunity)

    if status:
        query = query.filter(Opportunity.status == status)

    if customer_id:
        query = query.filter(Opportunity.customer_id == customer_id)

    total = query.count()

    # Pagination
    limit = min(limit, 500)  # Cap at 500
    opportunities = query.offset(offset).limit(limit).all()

    return {
        "opportunities": [OpportunityResponse.model_validate(o, from_attributes=True) for o in opportunities],
        "total": total,
        "offset": offset,
        "limit": limit
    }

# ============================================================================
# Customer Endpoints
# ============================================================================

@app.post("/customers", response_model=CustomerResponse, status_code=201)
@limiter.limit("30/minute")
async def create_customer(
    request,
    req: CustomerCreate,
    db: Session = Depends(get_db)
):
    """Create a customer"""
    payload = req.dict()
    payload["metadata_json"] = payload.pop("metadata", {})
    customer = Customer(**payload)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    logger.info(f"Created customer {customer.id}")
    return customer


@app.get("/customers/{customer_id}", response_model=CustomerResponse)
@limiter.limit("100/minute")
async def get_customer(request, customer_id: UUID, db: Session = Depends(get_db)):
    """Get customer by ID"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


# ============================================================================
# Task Status Endpoint (for Celery async tasks)
# ============================================================================

@app.get("/tasks/{task_id}")
@limiter.limit("10/minute")
async def get_task_status(request, task_id: str):
    """
    Poll async task status.

    Args:
        task_id: Task ID from message submission

    Returns:
        - status: pending, processing, completed, failed
        - result: Task result if completed
        - error: Error message if failed
    """
    # TODO: Implement task polling (Celery/BullMQ)
    return {
        "task_id": task_id,
        "status": "processing",
        "result": None,
        "error": None
    }

# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "code": "HTTP_ERROR",
            "path": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Generic exception handler for uncaught errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "path": str(request.url.path)
        }
    )

# ============================================================================
# Startup / Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Initializing TouchCLI Agent Service...")

    # Initialize database tables
    try:
        init_db()
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # TODO: Initialize Redis connection
    # TODO: Initialize LangGraph Router
    # TODO: Start Celery worker

    logger.info("TouchCLI Agent Service startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down TouchCLI Agent Service...")

    # TODO: Close database connections (handled by engine.dispose())
    # TODO: Close Redis connections
    # TODO: Shutdown Celery worker gracefully

    engine.dispose()
    logger.info("TouchCLI Agent Service shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("AGENT_SERVICE_PORT", 8000))
    )
