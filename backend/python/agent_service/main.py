"""
TouchCLI Agent Service - FastAPI Backend
Phase 2: Backend Infrastructure Implementation
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import desc
import os
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import logging

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


app = FastAPI(
    title="TouchCLI Agent Service",
    version="1.0.0",
    description="Conversational Sales Assistant Backend"
)

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
async def login(user_id: UUID, db: Session = Depends(get_db)):
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

    db_health = await get_db_health()

    # Check cache (Redis) - for now simplified
    redis_ok = True
    try:
        # TODO: Implement actual Redis health check when Redis is available
        pass
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_ok = False

    # Determine overall status
    overall_status = "ok"
    if db_health["status"] == "error" or not redis_ok:
        overall_status = "unhealthy"
    elif db_health["status"] == "degraded":
        overall_status = "degraded"

    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        checks={
            "database": ComponentHealth(
                status=db_health["status"],
                latency_ms=db_health.get("latency_ms"),
                last_checked=datetime.fromisoformat(db_health["last_checked"].replace("Z", "+00:00"))
            ),
            "agent_service": ComponentHealth(
                status="ok",
                latency_ms=0,
                last_checked=datetime.utcnow()
            ),
            "cache": ComponentHealth(
                status="ok" if redis_ok else "error",
                latency_ms=None,
                last_checked=datetime.utcnow()
            )
        }
    )

# ============================================================================
# Conversation Endpoints
# ============================================================================

@app.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    req: ConversationCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user)
):
    """
    Start a new conversation.

    Args:
        customer_id: Optional customer UUID for context
        opportunity_id: Optional opportunity UUID for context

    Returns:
        Conversation object with metadata
    """

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
        mode=req.mode
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    logger.info(f"Created conversation {conversation.id} for user {user_id}")
    return conversation


@app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
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
async def send_message(
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
async def get_messages(
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
async def create_opportunity(
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
        metadata=req.metadata
    )
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)

    logger.info(f"Created opportunity {opportunity.id} for customer {req.customer_id}")
    return opportunity


@app.get("/opportunities")
async def list_opportunities(
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
async def create_customer(
    req: CustomerCreate,
    db: Session = Depends(get_db)
):
    """Create a customer"""
    customer = Customer(**req.dict())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    logger.info(f"Created customer {customer.id}")
    return customer


@app.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: UUID, db: Session = Depends(get_db)):
    """Get customer by ID"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


# ============================================================================
# Task Status Endpoint (for Celery async tasks)
# ============================================================================

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
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
