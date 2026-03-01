-- TouchCLI PostgreSQL Schema - Initial Setup
-- Phase 1: Database Fundamentals
-- Created: 2026-03-02
-- Alembic Migration: db/migrations/versions/001_initial_schema.py

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search

-- Users & Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('sales', 'manager', 'admin')),
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),

    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

-- Customers (B2C: 医美顾客 | B2B: 客户公司)
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('individual', 'company')),
    phone VARCHAR(20),
    email VARCHAR(255),
    address TEXT,

    -- For B2C medical beauty
    beauty_type VARCHAR(100),  -- 美容项目类型
    service_history TEXT,       -- 服务历史

    -- For B2B
    company_size VARCHAR(50),
    industry VARCHAR(100),

    -- Shared fields
    tags JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Association
    assigned_to UUID NOT NULL REFERENCES users(id),
    owner_id UUID NOT NULL REFERENCES users(id),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id),

    -- Full-text search vector
    search_vector TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('chinese', name), 'A') ||
        setweight(to_tsvector('chinese', COALESCE(email, '')), 'B') ||
        setweight(to_tsvector('chinese', COALESCE(phone, '')), 'B')
    ) STORED
);
CREATE INDEX idx_customers_assigned_to ON customers(assigned_to);
CREATE INDEX idx_customers_owner_id ON customers(owner_id);
CREATE INDEX idx_customers_type ON customers(type);
CREATE INDEX idx_customers_created_at ON customers(created_at DESC);
CREATE INDEX idx_customers_search ON customers USING GIN(search_vector);

-- Opportunities (商机 / 交易)
CREATE TABLE opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id),
    amount DECIMAL(15, 2),
    currency VARCHAR(3) DEFAULT 'CNY',

    status VARCHAR(50) NOT NULL CHECK (status IN (
        'lead',        -- 线索
        'qualified',   -- 已转化
        'proposal',    -- 已发提案
        'negotiation', -- 协商中
        'won',         -- 已赢单
        'lost',        -- 已失单
        'on_hold'      -- 暂停
    )),

    stage_name VARCHAR(100),  -- 销售阶段名称（客户自定义）
    probability DECIMAL(3, 2) DEFAULT 0.5,  -- 成交概率 0-1

    expected_close_date DATE,
    actual_close_date DATE,

    owner_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id),

    notes TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX idx_opportunities_customer_id ON opportunities(customer_id);
CREATE INDEX idx_opportunities_owner_id ON opportunities(owner_id);
CREATE INDEX idx_opportunities_status ON opportunities(status);
CREATE INDEX idx_opportunities_created_at ON opportunities(created_at DESC);
CREATE INDEX idx_opportunities_expected_close ON opportunities(expected_close_date);

-- Conversations (对话历史)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- Context binding (对话可关联客户或商机)
    customer_id UUID REFERENCES customers(id),
    opportunity_id UUID REFERENCES opportunities(id),

    title VARCHAR(255),
    mode VARCHAR(50) NOT NULL CHECK (mode IN ('text', 'voice', 'hybrid')),

    status VARCHAR(50) NOT NULL CHECK (status IN (
        'active',      -- 进行中
        'completed',   -- 已完成
        'archived'     -- 已归档
    )),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    metadata JSONB DEFAULT '{}'::jsonb  -- 存储 Agent 上下文、参与者列表等
);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_customer_id ON conversations(customer_id);
CREATE INDEX idx_conversations_opportunity_id ON conversations(opportunity_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);

-- Messages (对话消息)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'agent', 'system')),
    agent_name VARCHAR(100),  -- Router / Sales / Data / Strategy / Sentinel / Memory 等

    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text' CHECK (content_type IN ('text', 'audio', 'structured')),

    -- 对于 Agent action
    action_type VARCHAR(100),  -- 如 create_opportunity, update_customer, execute_query
    action_status VARCHAR(50),  -- pending / executing / completed / failed
    action_result JSONB,

    embeddings VECTOR(1536),  -- 存储消息的向量表示（用于语义搜索）

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_messages_embeddings ON messages USING HNSW (embeddings vector_cosine_ops);

-- Agent State & Checkpoints (LangGraph checkpoint 持久化)
CREATE TABLE agent_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    agent_type VARCHAR(100) NOT NULL CHECK (agent_type IN (
        'router', 'sales', 'data', 'strategy', 'sentinel', 'memory'
    )),

    -- LangGraph checkpoint 数据
    checkpoint_id VARCHAR(255),
    checkpoint_data JSONB NOT NULL,  -- 存储 Agent 的完整状态

    -- 执行信息
    input_data JSONB,
    output_data JSONB,
    execution_time_ms INTEGER,

    status VARCHAR(50) DEFAULT 'completed' CHECK (status IN (
        'pending', 'executing', 'completed', 'failed'
    )),
    error_message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 审计
    updated_by VARCHAR(100),
    metadata JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX idx_agent_states_conversation_id ON agent_states(conversation_id);
CREATE INDEX idx_agent_states_agent_type ON agent_states(agent_type);
CREATE INDEX idx_agent_states_created_at ON agent_states(created_at DESC);

-- Activity Log (审计日志)
CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    agent_name VARCHAR(100),  -- 如果由 Agent 触发

    entity_type VARCHAR(100) NOT NULL,  -- customer, opportunity, message, etc.
    entity_id UUID NOT NULL,

    action VARCHAR(100) NOT NULL CHECK (action IN (
        'create', 'update', 'delete', 'view', 'export'
    )),

    old_values JSONB,
    new_values JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX idx_activity_log_user_id ON activity_log(user_id);
CREATE INDEX idx_activity_log_entity ON activity_log(entity_type, entity_id);
CREATE INDEX idx_activity_log_created_at ON activity_log(created_at DESC);

-- Session Cache (用于 Redis 中存储的会话数据备份)
CREATE TABLE session_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    conversation_id UUID REFERENCES conversations(id),

    session_data JSONB NOT NULL,  -- 从 Redis 定期快照的数据

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,

    CONSTRAINT expires_at_check CHECK (expires_at IS NULL OR expires_at > created_at)
);
CREATE INDEX idx_session_snapshots_user_id ON session_snapshots(user_id);
CREATE INDEX idx_session_snapshots_expires_at ON session_snapshots(expires_at);

-- Batch Job Tracking (异步任务追踪)
CREATE TABLE batch_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(100) NOT NULL,  -- export, sync, notification, etc.

    status VARCHAR(50) NOT NULL CHECK (status IN (
        'queued', 'running', 'completed', 'failed'
    )),

    parameters JSONB,
    result JSONB,
    error_message TEXT,

    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    created_by UUID REFERENCES users(id),
    metadata JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX idx_batch_jobs_status ON batch_jobs(status);
CREATE INDEX idx_batch_jobs_created_at ON batch_jobs(created_at DESC);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER update_users_timestamp BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_customers_timestamp BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_opportunities_timestamp BEFORE UPDATE ON opportunities
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_conversations_timestamp BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_agent_states_timestamp BEFORE UPDATE ON agent_states
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_batch_jobs_timestamp BEFORE UPDATE ON batch_jobs
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- Grant permissions (假设 app user 是 touchcli_app)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO touchcli_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO touchcli_app;
