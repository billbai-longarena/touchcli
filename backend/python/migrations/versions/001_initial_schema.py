"""Initial schema from Phase 1 database design

Revision ID: 001_initial
Revises:
Create Date: 2026-03-02

Creates all core tables:
- users, customers, opportunities, conversations, messages
- agent_states, activity_log, session_snapshots, batch_jobs
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema"""

    # Create custom types/enums
    user_role = postgresql.ENUM('admin', 'manager', 'salesperson', 'analyst', name='user_role')
    user_role.create(op.get_bind(), checkfirst=True)

    conversation_mode = postgresql.ENUM('text', 'voice', 'hybrid', name='conversation_mode')
    conversation_mode.create(op.get_bind(), checkfirst=True)

    conversation_status = postgresql.ENUM('active', 'paused', 'completed', 'archived', name='conversation_status')
    conversation_status.create(op.get_bind(), checkfirst=True)

    customer_type = postgresql.ENUM('individual', 'company', name='customer_type')
    customer_type.create(op.get_bind(), checkfirst=True)

    opportunity_status = postgresql.ENUM('discovery', 'proposal', 'negotiation', 'closed_won', 'closed_lost', name='opportunity_status')
    opportunity_status.create(op.get_bind(), checkfirst=True)

    agent_type = postgresql.ENUM('router', 'sales', 'data', 'strategy', 'sentinel', 'memory', name='agent_type')
    agent_type.create(op.get_bind(), checkfirst=True)

    activity_action = postgresql.ENUM('create', 'update', 'delete', 'view', 'export', name='activity_action')
    activity_action.create(op.get_bind(), checkfirst=True)

    job_status = postgresql.ENUM('pending', 'running', 'completed', 'failed', name='job_status')
    job_status.create(op.get_bind(), checkfirst=True)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', user_role, nullable=False, server_default='salesperson'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('email', name='uq_users_email'),
        sa.Index('idx_users_email', 'email'),
        sa.Index('idx_users_role', 'role'),
    )

    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('type', customer_type, nullable=False, server_default='company'),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(20)),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('tags', postgresql.JSON(), server_default='[]'),
        sa.Column('metadata', postgresql.JSON(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index('idx_customers_name', 'name'),
        sa.Index('idx_customers_email', 'email'),
        sa.Index('idx_customers_phone', 'phone'),
        sa.Index('idx_customers_assigned_to', 'assigned_to'),
    )

    # Create opportunities table
    op.create_table(
        'opportunities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), server_default='CNY'),
        sa.Column('status', opportunity_status, nullable=False, server_default='discovery'),
        sa.Column('probability', sa.Float(), server_default='0.0'),
        sa.Column('expected_close_date', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('metadata', postgresql.JSON(), server_default='{}'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.Index('idx_opportunities_customer_id', 'customer_id'),
        sa.Index('idx_opportunities_name', 'name'),
        sa.Index('idx_opportunities_status', 'status'),
    )

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True)),
        sa.Column('opportunity_id', postgresql.UUID(as_uuid=True)),
        sa.Column('mode', conversation_mode, nullable=False, server_default='text'),
        sa.Column('status', conversation_status, nullable=False, server_default='active'),
        sa.Column('summary_text', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id']),
        sa.Index('idx_conversations_user_id', 'user_id'),
        sa.Index('idx_conversations_customer_id', 'customer_id'),
        sa.Index('idx_conversations_status', 'status'),
        sa.Index('idx_conversations_created_at', 'created_at'),
    )

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True)),
        sa.Column('sender_role', sa.String(50)),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_type', sa.String(50), server_default='text'),
        sa.Column('attachments', postgresql.JSON(), server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id', ], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id']),
        sa.Index('idx_messages_conversation_id', 'conversation_id'),
        sa.Index('idx_messages_created_at', 'created_at'),
    )

    # Create agent_states table
    op.create_table(
        'agent_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_type', agent_type, nullable=False),
        sa.Column('state', postgresql.JSON(), nullable=False),
        sa.Column('checkpoint_id', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('conversation_id', 'agent_type', name='unique_conversation_agent'),
        sa.Index('idx_agent_states_conversation_agent', 'conversation_id', 'agent_type'),
    )

    # Create activity_log table
    op.create_table(
        'activity_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', activity_action, nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True)),
        sa.Column('changes', postgresql.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id']),
        sa.Index('idx_activity_log_entity', 'entity_type', 'entity_id'),
        sa.Index('idx_activity_log_actor', 'actor_id'),
        sa.Index('idx_activity_log_created', 'created_at'),
    )

    # Create session_snapshots table
    op.create_table(
        'session_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('state', postgresql.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.Index('idx_session_snapshots_user_conversation', 'user_id', 'conversation_id'),
        sa.Index('idx_session_snapshots_created', 'created_at'),
    )

    # Create batch_jobs table
    op.create_table(
        'batch_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('status', job_status, nullable=False, server_default='pending'),
        sa.Column('parameters', postgresql.JSON()),
        sa.Column('result', postgresql.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Index('idx_batch_jobs_type_status', 'job_type', 'status'),
        sa.Index('idx_batch_jobs_created', 'created_at'),
    )


def downgrade() -> None:
    """Drop all tables"""
    op.drop_table('batch_jobs')
    op.drop_table('session_snapshots')
    op.drop_table('activity_log')
    op.drop_table('agent_states')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('opportunities')
    op.drop_table('customers')
    op.drop_table('users')

    # Drop enums
    for enum_name in ['user_role', 'conversation_mode', 'conversation_status', 'customer_type',
                      'opportunity_status', 'agent_type', 'activity_action', 'job_status']:
        op.execute(f'DROP TYPE IF EXISTS {enum_name}')
