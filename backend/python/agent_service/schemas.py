"""
Pydantic request/response schemas for TouchCLI API
Validates input data and serializes output responses
"""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ============================================================================
# User Schemas
# ============================================================================

class UserCreate(BaseModel):
    """User creation request"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="salesperson", pattern="^(admin|manager|salesperson|analyst)$")


class UserUpdate(BaseModel):
    """User update request"""
    name: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, pattern="^(admin|manager|salesperson|analyst)$")


class UserResponse(BaseModel):
    """User response"""
    id: UUID
    email: str
    name: str
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Customer Schemas
# ============================================================================

class CustomerCreate(BaseModel):
    """Customer creation request"""
    type: str = Field(default="company", pattern="^(individual|company)$")
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    assigned_to: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CustomerUpdate(BaseModel):
    """Customer update request"""
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    assigned_to: Optional[UUID] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class CustomerResponse(BaseModel):
    """Customer response"""
    id: UUID
    type: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    assigned_to: Optional[UUID]
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerDetail(CustomerResponse):
    """Detailed customer response with related data"""
    opportunities_count: Optional[int] = None
    active_conversations_count: Optional[int] = None


# ============================================================================
# Opportunity Schemas
# ============================================================================

class OpportunityCreate(BaseModel):
    """Opportunity creation request"""
    customer_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    amount: float = Field(..., gt=0)
    currency: str = Field(default="CNY", max_length=3)
    status: str = Field(default="discovery", pattern="^(discovery|proposal|negotiation|closed_won|closed_lost)$")
    probability: float = Field(default=0.0, ge=0.0, le=1.0)
    expected_close_date: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OpportunityUpdate(BaseModel):
    """Opportunity update request"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[str] = Field(None, pattern="^(discovery|proposal|negotiation|closed_won|closed_lost)$")
    probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    expected_close_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class OpportunityResponse(BaseModel):
    """Opportunity response"""
    id: UUID
    customer_id: UUID
    name: str
    description: Optional[str]
    amount: float
    currency: str
    status: str
    probability: float
    expected_close_date: Optional[datetime]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OpportunityDetail(OpportunityResponse):
    """Detailed opportunity response with related customer"""
    customer: Optional[CustomerResponse] = None


# ============================================================================
# Conversation Schemas
# ============================================================================

class ConversationCreate(BaseModel):
    """Conversation creation request"""
    customer_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    mode: str = Field(default="text", pattern="^(text|voice|hybrid)$")


class ConversationUpdate(BaseModel):
    """Conversation update request"""
    status: Optional[str] = Field(None, pattern="^(active|paused|completed|archived)$")
    summary_text: Optional[str] = None


class ConversationResponse(BaseModel):
    """Conversation response"""
    id: UUID
    user_id: UUID
    customer_id: Optional[UUID]
    opportunity_id: Optional[UUID]
    mode: str
    status: str
    summary_text: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationDetail(ConversationResponse):
    """Detailed conversation response with related data"""
    messages_count: Optional[int] = None
    agent_states: Optional[Dict[str, Any]] = None


# ============================================================================
# Message Schemas
# ============================================================================

class MessageCreate(BaseModel):
    """Message creation request"""
    conversation_id: UUID
    content: str = Field(..., min_length=1)
    content_type: str = Field(default="text", pattern="^(text|voice|image|video|attachment)$")
    attachments: List[Dict[str, Any]] = Field(default_factory=list)


class MessageResponse(BaseModel):
    """Message response"""
    id: UUID
    conversation_id: UUID
    sender_id: Optional[UUID]
    sender_role: Optional[str]
    content: str
    content_type: str
    attachments: List[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Agent & State Schemas
# ============================================================================

class AgentStateResponse(BaseModel):
    """Agent state response"""
    id: UUID
    conversation_id: UUID
    agent_type: str
    state: Dict[str, Any]
    checkpoint_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Health Check Schemas
# ============================================================================

class ComponentHealth(BaseModel):
    """Component health status"""
    status: str = Field(..., pattern="^(ok|degraded|error)$")
    latency_ms: Optional[int] = None
    last_checked: datetime


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., pattern="^(ok|degraded|unhealthy)$")
    timestamp: datetime
    version: str
    checks: Dict[str, ComponentHealth]


# ============================================================================
# Pagination Schemas
# ============================================================================

class PaginationResponse(BaseModel):
    """Generic pagination response"""
    total: int
    limit: int
    offset: int
    items: List[Any]


class MessageListResponse(BaseModel):
    """Message list with pagination"""
    messages: List[MessageResponse]
    total: int
    limit: int
    offset: int


class OpportunityListResponse(BaseModel):
    """Opportunity list with pagination"""
    opportunities: List[OpportunityResponse]
    total: int
    limit: int
    offset: int


# ============================================================================
# Task & Job Schemas
# ============================================================================

class TaskResponse(BaseModel):
    """Async task status response"""
    task_id: str
    status: str = Field(..., pattern="^(pending|processing|completed|failed)$")
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskStatusRequest(BaseModel):
    """Request to poll task status"""
    task_id: str


# ============================================================================
# Error Response Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    code: str
    path: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
