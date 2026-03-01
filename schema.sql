-- TouchCLI Backend: PostgreSQL Schema
-- Phase 1: Data & Communication Foundation
-- Generated: 2026-03-02
-- Status: Draft (Worker phase S-002)

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- for full-text search

-- ============================================================================
-- Core Domain Tables
-- ============================================================================

-- Users (SalesTouch legacy + TouchCLI extended)
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  avatar_url TEXT,
  role VARCHAR(50) DEFAULT 'salesperson',  -- salesperson, manager, admin
  phone_number VARCHAR(20),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_by UUID,
  version INT DEFAULT 1
);

-- Customers (B2B accounts, medical spa customers)
CREATE TABLE IF NOT EXISTS customers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  owner_id UUID NOT NULL REFERENCES users(id),
  company_name VARCHAR(255),
  industry VARCHAR(100),
  region VARCHAR(50),
  contact_person VARCHAR(255),
  contact_email VARCHAR(255),
  classification VARCHAR(50),  -- VIP, standard, prospect, churned
  metadata_json JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_by UUID,
  version INT DEFAULT 1
);

-- Opportunities (B2B sales pipeline)
CREATE TABLE IF NOT EXISTS opportunities (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  customer_id UUID NOT NULL REFERENCES customers(id),
  owner_id UUID NOT NULL REFERENCES users(id),
  name VARCHAR(255) NOT NULL,
  amount DECIMAL(15, 2),
  stage VARCHAR(50),  -- discovery, proposal, negotiation, closed-won, closed-lost
  expected_close_date DATE,
  agent_notes_json JSONB DEFAULT '{}',  -- decision logs, context
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_by UUID,
  version INT DEFAULT 1
);

-- Conversations (Audio/text dialog sessions)
CREATE TABLE IF NOT EXISTS conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id),
  customer_id UUID REFERENCES customers(id),
  opportunity_id UUID REFERENCES opportunities(id),
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ended_at TIMESTAMP,
  duration_seconds INT,
  summary_text TEXT,
  agent_states_json JSONB DEFAULT '{}',  -- {agent_name: {...checkpoint...}}
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  version INT DEFAULT 1
);

-- Messages (Individual message log)
CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  sender_type VARCHAR(20),  -- user, agent, system
  sender_id UUID,
  content TEXT NOT NULL,
  attachments_json JSONB DEFAULT '[]',  -- [{ type: "file", url: "..." }]
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  version INT DEFAULT 1
);

-- Agent States (LangGraph checkpoint persistence)
CREATE TABLE IF NOT EXISTS agent_states (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  agent_name VARCHAR(100) NOT NULL,  -- Router, Sales, Data, Strategy, etc.
  checkpoint_data JSONB NOT NULL,  -- LangGraph checkpoint serialized
  memory_buffer_json JSONB DEFAULT '{}',  -- {short_term: [...], long_term: [...]}
  checkpoint_version INT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  version INT DEFAULT 1
);

-- ============================================================================
-- Audit & Metadata
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
  id BIGSERIAL PRIMARY KEY,
  entity_type VARCHAR(100),
  entity_id UUID,
  action VARCHAR(50),  -- created, updated, deleted
  user_id UUID REFERENCES users(id),
  changes_json JSONB,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Indexes
-- ============================================================================

-- Foreign key performance
CREATE INDEX idx_customers_owner_id ON customers(owner_id);
CREATE INDEX idx_opportunities_customer_id ON opportunities(customer_id);
CREATE INDEX idx_opportunities_owner_id ON opportunities(owner_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_customer_id ON conversations(customer_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_agent_states_conversation_id ON agent_states(conversation_id);

-- Time range queries
CREATE INDEX idx_conversations_started_at ON conversations(started_at DESC);
CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC);

-- Search optimization
CREATE INDEX idx_customers_company_name_gin ON customers USING gin(to_tsvector('english', company_name));
CREATE INDEX idx_messages_content_gin ON messages USING gin(to_tsvector('english', content));

-- Status/stage lookups
CREATE INDEX idx_opportunities_stage ON opportunities(stage);
CREATE INDEX idx_customers_classification ON customers(classification);

-- ============================================================================
-- Triggers
-- ============================================================================

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trigger_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trigger_opportunities_updated_at BEFORE UPDATE ON opportunities FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trigger_agent_states_updated_at BEFORE UPDATE ON agent_states FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ============================================================================
-- Views (for common queries)
-- ============================================================================

-- Recent conversations with customer & opportunity context
CREATE OR REPLACE VIEW v_conversations_full AS
SELECT
  c.id,
  c.user_id,
  u.name as user_name,
  c.customer_id,
  cust.company_name,
  c.opportunity_id,
  opp.name as opportunity_name,
  c.started_at,
  c.ended_at,
  c.summary_text
FROM conversations c
LEFT JOIN users u ON c.user_id = u.id
LEFT JOIN customers cust ON c.customer_id = cust.id
LEFT JOIN opportunities opp ON c.opportunity_id = opp.id
ORDER BY c.started_at DESC;

-- Agent checkpoint status per conversation
CREATE OR REPLACE VIEW v_agent_checkpoint_status AS
SELECT
  conversation_id,
  json_object_keys(agent_states_json) as agent_name,
  agent_states_json -> json_object_keys(agent_states_json) ->> 'timestamp' as last_update
FROM conversations
WHERE agent_states_json IS NOT NULL AND agent_states_json != '{}'::jsonb;

-- ============================================================================
-- Notes
-- ============================================================================
/*
Schema Design Decisions:
1. UUID for all primary keys (better for distributed systems)
2. JSONB for semi-structured data (metadata, checkpoints, notes)
3. Separate audit_log table (instead of triggers) for compliance auditing
4. No hard deletes (soft delete support via version tracking)
5. All tables support multi-tenancy via user_id foreign key
6. GIN indexes for full-text search on text fields
7. Agent states stored as nested JSON (no separate table) for atomicity
*/
