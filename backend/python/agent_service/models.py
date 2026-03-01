"""
SQLAlchemy ORM Models for TouchCLI Agent Service
Maps to Phase 1 schema (db/001_initial_schema.sql)
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Numeric, ForeignKey, Index, UniqueConstraint, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """User model - Sales agents and team members"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    avatar_url = Column(Text)
    role = Column(String(50), default="salesperson", index=True)
    preferred_locale = Column(String(10), default="en-US", index=True)
    phone_number = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    version = Column(Integer, default=1)

    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    activities = relationship("ActivityLog", back_populates="user")

    __table_args__ = (
        Index("idx_users_role", "role"),
        Index("idx_users_preferred_locale", "preferred_locale"),
        Index("idx_users_created_at", "created_at"),
    )


class Customer(Base):
    """Customer model"""
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(20))
    company = Column(String(255), index=True)
    industry = Column(String(100))
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relationships
    opportunities = relationship("Opportunity", back_populates="customer")
    conversations = relationship("Conversation", back_populates="customer")

    __table_args__ = (
        Index("idx_customers_name", "name"),
        Index("idx_customers_company", "company"),
    )


class Opportunity(Base):
    """Sales opportunity model"""
    __tablename__ = "opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    title = Column(String(255), nullable=False)
    stage = Column(String(50), default="prospecting", index=True)
    value = Column(Numeric(12, 2))
    close_date = Column(DateTime)
    notes = Column(Text)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relationships
    customer = relationship("Customer", back_populates="opportunities")
    conversations = relationship("Conversation", back_populates="opportunity")

    __table_args__ = (
        Index("idx_opportunities_customer_id", "customer_id"),
        Index("idx_opportunities_stage", "stage"),
    )


class Conversation(Base):
    """Conversation model"""
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"))
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    title = Column(String(255))
    mode = Column(String(50), default="text", index=True)
    type = Column(String(50), default="sales", index=True)
    locale = Column(String(10), default="en-US", index=True)
    status = Column(String(50), default="active", index=True)
    summary_text = Column(Text)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relationships
    user = relationship("User", back_populates="conversations")
    customer = relationship("Customer", back_populates="conversations")
    opportunity = relationship("Opportunity", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    agent_states = relationship("AgentState", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_conversations_user_id", "user_id"),
        Index("idx_conversations_customer_id", "customer_id"),
        Index("idx_conversations_locale", "locale"),
        Index("idx_conversations_status", "status"),
    )


class Message(Base):
    """Message model"""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    sender = Column(String(50), nullable=False)  # user, agent, system
    content = Column(Text, nullable=False)
    role = Column(String(50))  # user, assistant, system (for LLM compatibility)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_sender", "sender"),
        Index("idx_messages_created_at", "created_at"),
    )


class AgentState(Base):
    """Agent state checkpoint for LangGraph"""
    __tablename__ = "agent_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    checkpoint_id = Column(String(255))
    state_data = Column(JSON, nullable=False)  # Serialized LangGraph state
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relationships
    conversation = relationship("Conversation", back_populates="agent_states")

    __table_args__ = (
        Index("idx_agent_states_conversation_id", "conversation_id"),
        Index("idx_agent_states_agent_name", "agent_name"),
    )


class ActivityLog(Base):
    """Activity audit log"""
    __tablename__ = "activity_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(UUID(as_uuid=True))
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relationships
    user = relationship("User", back_populates="activities")

    __table_args__ = (
        Index("idx_activity_log_user_id", "user_id"),
        Index("idx_activity_log_action", "action"),
        Index("idx_activity_log_created_at", "created_at"),
    )


class SessionSnapshot(Base):
    """User session snapshots"""
    __tablename__ = "session_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    __table_args__ = (
        Index("idx_session_snapshots_user_id", "user_id"),
        Index("idx_session_snapshots_is_active", "is_active"),
    )


class BatchJob(Base):
    """Async batch job tracking (for Celery)"""
    __tablename__ = "batch_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String(255), unique=True, nullable=False)
    job_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    progress = Column(Numeric(5, 2), default=0)  # 0-100
    input_params = Column(JSON)
    result = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    __table_args__ = (
        Index("idx_batch_jobs_status", "status"),
        Index("idx_batch_jobs_task_id", "task_id"),
    )
