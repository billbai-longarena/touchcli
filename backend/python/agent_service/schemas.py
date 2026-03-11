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
    role: str = Field(
        default="salesperson", pattern="^(admin|manager|salesperson|analyst)$"
    )
    preferred_locale: str = Field(default="en-US", pattern="^[a-z]{2}-[A-Z]{2}$")


class UserUpdate(BaseModel):
    """User update request"""

    name: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, pattern="^(admin|manager|salesperson|analyst)$")
    preferred_locale: Optional[str] = Field(None, pattern="^[a-z]{2}-[A-Z]{2}$")


class UserResponse(BaseModel):
    """User response"""

    id: UUID
    email: str
    name: str
    role: str
    preferred_locale: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Authentication Schemas
# ============================================================================


class PasswordLoginRequest(BaseModel):
    """Password login request"""

    account: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=255)


class SendSmsCodeRequest(BaseModel):
    """SMS verification code request"""

    phone: str = Field(..., min_length=3, max_length=32)


class SmsLoginRequest(BaseModel):
    """SMS login request"""

    phone: str = Field(..., min_length=3, max_length=32)
    code: str = Field(..., min_length=4, max_length=6)


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
    metadata: Dict[str, Any] = Field(alias="metadata_json")
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
    title: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    stage: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)  # alias for stage
    probability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    notes: Optional[str] = None
    close_date: Optional[datetime] = None

    @field_validator("stage", mode="before")
    @classmethod
    def resolve_stage(cls, v: Optional[str], info) -> Optional[str]:
        return v

    def get_stage(self) -> str:
        """Return stage, falling back to status, then default."""
        return self.stage or self.status or "prospecting"


class OpportunityUpdate(BaseModel):
    """Opportunity update request"""

    title: Optional[str] = Field(None, max_length=255)
    amount: Optional[float] = Field(None, gt=0)
    stage: Optional[str] = None
    notes: Optional[str] = None
    close_date: Optional[datetime] = None


class OpportunityResponse(BaseModel):
    """Opportunity response"""

    id: UUID
    customer_id: UUID
    title: str
    amount: float = Field(validation_alias="value")
    stage: str
    status: str = Field(default="")  # mirror of stage for compatibility
    probability: Optional[float] = None
    notes: Optional[str] = None
    close_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        instance = super().model_validate(obj, *args, **kwargs)
        # Mirror stage -> status
        if not instance.status:
            instance.status = instance.stage
        # Convert Decimal probability to float
        if hasattr(obj, "probability") and obj.probability is not None:
            instance.probability = float(obj.probability)
        return instance

    class Config:
        from_attributes = True
        populate_by_name = True


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
    title: Optional[str] = Field(None, max_length=255)
    mode: str = Field(default="text", pattern="^(text|voice|hybrid)$")
    locale: Optional[str] = Field(default=None, pattern="^[a-z]{2}-[A-Z]{2}$")


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
    title: Optional[str] = None
    locale: Optional[str]
    mode: str
    type: Optional[str] = None
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
    content_type: str = Field(
        default="text", pattern="^(text|voice|image|video|attachment)$"
    )
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
