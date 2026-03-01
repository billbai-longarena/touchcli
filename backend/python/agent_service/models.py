"""
SQLAlchemy ORM Models for TouchCLI
Maps Phase 1 database schema to Python models
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, UUID,
    ForeignKey, Index, Enum, UniqueConstraint, CheckConstraint, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

Base = declarative_base()


# ============================================================================
# Enums
# ============================================================================

class UserRole(str, enum.Enum):
    """User role enumeration"""
    admin = "admin"
    manager = "manager"
    salesperson = "salesperson"
    analyst = "analyst"


class ConversationMode(str, enum.Enum):
    """Conversation mode enumeration"""
    text = "text"
    voice = "voice"
    hybrid = "hybrid"


class ConversationStatus(str, enum.Enum):
    """Conversation status enumeration"""
    active = "active"
    paused = "paused"
    completed = "completed"
    archived = "archived"


class CustomerType(str, enum.Enum):
    """Customer type enumeration"""
    individual = "individual"
    company = "company"


class OpportunityStatus(str, enum.Enum):
    """Opportunity sales stage enumeration"""
    discovery = "discovery"
    proposal = "proposal"
    negotiation = "negotiation"
    closed_won = "closed_won"
    closed_lost = "closed_lost"


class AgentType(str, enum.Enum):
    """Agent type enumeration"""
    router = "router"
    sales = "sales"
    data = "data"
    strategy = "strategy"
    sentinel = "sentinel"
    memory = "memory"


class ActivityAction(str, enum.Enum):
    """Activity log action enumeration"""
    create = "create"
    update = "update"
    delete = "delete"
    view = "view"
    export = "export"


class JobStatus(str, enum.Enum):
    """Batch job status enumeration"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


# ============================================================================
# User & Authentication
# ============================================================================

class User(Base):
    """User account model"""
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.salesperson)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    conversations = relationship("Conversation", back_populates="user", foreign_keys="Conversation.user_id")
    messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    customers = relationship("Customer", back_populates="assigned_to_user")
    activity_logs = relationship("ActivityLog", back_populates="actor")

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_role", "role"),
        CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'", name="valid_email"),
    )


# ============================================================================
# Customer & Opportunity
# ============================================================================

class Customer(Base):
    """Customer model"""
    __tablename__ = "customers"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    type = Column(Enum(CustomerType), nullable=False, default=CustomerType.company)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), index=True)
    phone = Column(String(20), index=True)
    assigned_to = Column(UUID, ForeignKey("users.id"), nullable=True)
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    assigned_to_user = relationship("User", back_populates="customers")
    opportunities = relationship("Opportunity", back_populates="customer")
    conversations = relationship("Conversation", back_populates="customer")
    activity_logs = relationship("ActivityLog", back_populates="customer", foreign_keys="ActivityLog.entity_id")

    __table_args__ = (
        Index("idx_customers_name", "name"),
        Index("idx_customers_email", "email"),
        Index("idx_customers_phone", "phone"),
        Index("idx_customers_assigned_to", "assigned_to"),
    )


class Opportunity(Base):
    """Opportunity (sales deal) model"""
    __tablename__ = "opportunities"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="CNY")
    status = Column(Enum(OpportunityStatus), nullable=False, default=OpportunityStatus.discovery, index=True)
    probability = Column(Float, default=0.0)
    expected_close_date = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    metadata = Column(JSON, default=dict)

    # Relationships
    customer = relationship("Customer", back_populates="opportunities")
    conversations = relationship("Conversation", back_populates="opportunity")
    activity_logs = relationship("ActivityLog", back_populates="opportunity", foreign_keys="ActivityLog.entity_id")

    __table_args__ = (
        Index("idx_opportunities_customer_id", "customer_id"),
        Index("idx_opportunities_name", "name"),
        Index("idx_opportunities_status", "status"),
        CheckConstraint("amount > 0", name="positive_amount"),
        CheckConstraint("probability >= 0 AND probability <= 1", name="valid_probability"),
    )


# ============================================================================
# Conversation & Messages
# ============================================================================

class Conversation(Base):
    """Conversation model"""
    __tablename__ = "conversations"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=True, index=True)
    opportunity_id = Column(UUID, ForeignKey("opportunities.id"), nullable=True, index=True)
    mode = Column(Enum(ConversationMode), nullable=False, default=ConversationMode.text)
    status = Column(Enum(ConversationStatus), nullable=False, default=ConversationStatus.active, index=True)
    summary_text = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="conversations", foreign_keys="Conversation.user_id")
    customer = relationship("Customer", back_populates="conversations")
    opportunity = relationship("Opportunity", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    agent_states = relationship("AgentState", back_populates="conversation", cascade="all, delete-orphan")
    session_snapshots = relationship("SessionSnapshot", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_conversations_user_id", "user_id"),
        Index("idx_conversations_customer_id", "customer_id"),
        Index("idx_conversations_status", "status"),
        Index("idx_conversations_created_at", "created_at"),
    )


class Message(Base):
    """Message model"""
    __tablename__ = "messages"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID, ForeignKey("conversations.id"), nullable=False, index=True)
    sender_id = Column(UUID, ForeignKey("users.id"), nullable=True, index=True)
    sender_role = Column(String(50))  # "user", "agent", "system"
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="text")  # "text", "voice", "image", etc.
    attachments = Column(JSON, default=list)
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", back_populates="messages", foreign_keys="Message.sender_id")

    __table_args__ = (
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_created_at", "created_at"),
    )


# ============================================================================
# Agent State & Checkpoints
# ============================================================================

class AgentState(Base):
    """Agent state checkpoint model"""
    __tablename__ = "agent_states"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID, ForeignKey("conversations.id"), nullable=False, index=True)
    agent_type = Column(Enum(AgentType), nullable=False, index=True)
    state = Column(JSON, nullable=False)
    checkpoint_id = Column(String(255), index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="agent_states")

    __table_args__ = (
        Index("idx_agent_states_conversation_agent", "conversation_id", "agent_type"),
        UniqueConstraint("conversation_id", "agent_type", name="unique_conversation_agent"),
    )


# ============================================================================
# Activity & Audit Log
# ============================================================================

class ActivityLog(Base):
    """Activity audit log model"""
    __tablename__ = "activity_log"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False, index=True)  # "customer", "opportunity", etc.
    entity_id = Column(UUID, nullable=False, index=True)
    action = Column(Enum(ActivityAction), nullable=False, index=True)
    actor_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    changes = Column(JSON)
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)

    # Relationships
    actor = relationship("User", back_populates="activity_logs")
    # Dynamic relationship to customer/opportunity
    customer = relationship("Customer", uselist=False, foreign_keys="ActivityLog.entity_id",
                           primaryjoin="and_(ActivityLog.entity_type=='customer', ActivityLog.entity_id==Customer.id)",
                           viewonly=True, back_populates="activity_logs")
    opportunity = relationship("Opportunity", uselist=False, foreign_keys="ActivityLog.entity_id",
                              primaryjoin="and_(ActivityLog.entity_type=='opportunity', ActivityLog.entity_id==Opportunity.id)",
                              viewonly=True, back_populates="activity_logs")

    __table_args__ = (
        Index("idx_activity_log_entity", "entity_type", "entity_id"),
        Index("idx_activity_log_actor", "actor_id"),
        Index("idx_activity_log_created", "created_at"),
    )


# ============================================================================
# Session & State Management
# ============================================================================

class SessionSnapshot(Base):
    """Session state snapshot for resumption"""
    __tablename__ = "session_snapshots"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(UUID, ForeignKey("conversations.id"), nullable=False, index=True)
    state = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="session_snapshots")

    __table_args__ = (
        Index("idx_session_snapshots_user_conversation", "user_id", "conversation_id"),
        Index("idx_session_snapshots_created", "created_at"),
    )


# ============================================================================
# Batch Jobs
# ============================================================================

class BatchJob(Base):
    """Batch job processing model (for exports, syncs, etc.)"""
    __tablename__ = "batch_jobs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False, index=True)  # "export", "sync", "cleanup", etc.
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.pending, index=True)
    parameters = Column(JSON)
    result = Column(JSON)
    created_at = Column(DateTime, nullable=False, default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    __table_args__ = (
        Index("idx_batch_jobs_type_status", "job_type", "status"),
        Index("idx_batch_jobs_created", "created_at"),
    )
