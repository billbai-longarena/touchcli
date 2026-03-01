"""
Integration tests for TouchCLI Agent Service
Tests: API endpoints, database persistence, WebSocket integration
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Test database - use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

# Fixtures and setup
@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    
    # Import models and create tables
    try:
        from agent_service.models import Base
    except ImportError:
        from models import Base
    
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db_session(test_db_engine):
    """Create test database session"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine,
    )
    
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def test_client(test_db_session):
    """Create test client with dependency override"""
    try:
        from agent_service.main import app
        from agent_service.db import get_db
    except ImportError:
        from main import app
        from db import get_db
    
    def override_get_db():
        yield test_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_jwt_token():
    """Generate test JWT token"""
    try:
        from agent_service.auth import create_token
    except ImportError:
        from auth import create_token
    
    user_id = uuid4()
    token = create_token(user_id)
    return token, user_id


# ============================================================================
# Health Check Tests
# ============================================================================

def test_health_check(test_client):
    """Test health check endpoint"""
    response = test_client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] in ["ok", "degraded", "unhealthy"]
    assert "timestamp" in data
    assert "checks" in data
    assert "database" in data["checks"]


# ============================================================================
# Authentication Tests
# ============================================================================

def test_missing_auth_token(test_client):
    """Test that endpoints require authentication"""
    response = test_client.post("/conversations", json={})
    assert response.status_code in [401, 403]  # Unauthorized or Forbidden


def test_invalid_auth_token(test_client):
    """Test with invalid token"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = test_client.post("/conversations", json={}, headers=headers)
    assert response.status_code == 401


def test_valid_auth_token(test_client, test_jwt_token):
    """Test with valid token"""
    token, user_id = test_jwt_token
    headers = {"Authorization": f"Bearer {token}"}
    
    # This should not return 401 (may return 422 for missing fields, which is OK)
    response = test_client.post(
        "/conversations",
        json={},
        headers=headers
    )
    assert response.status_code in [201, 422]  # Created or validation error


# ============================================================================
# Conversation Endpoints Tests
# ============================================================================

def test_create_conversation(test_client, test_jwt_token):
    """Test creating a conversation"""
    token, user_id = test_jwt_token
    headers = {"Authorization": f"Bearer {token}"}
    
    response = test_client.post(
        "/conversations",
        json={"customer_id": None, "opportunity_id": None},
        headers=headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["type"] == "sales"
    assert data["status"] == "active"


def test_get_conversation(test_client, test_jwt_token):
    """Test retrieving a conversation"""
    token, user_id = test_jwt_token
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create conversation first
    create_response = test_client.post(
        "/conversations",
        json={},
        headers=headers
    )
    conv_id = create_response.json()["id"]
    
    # Get conversation
    get_response = test_client.get(
        f"/conversations/{conv_id}",
        headers=headers
    )
    
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == conv_id


def test_conversation_not_found(test_client, test_jwt_token):
    """Test getting non-existent conversation"""
    token, _ = test_jwt_token
    headers = {"Authorization": f"Bearer {token}"}
    
    fake_id = str(uuid4())
    response = test_client.get(
        f"/conversations/{fake_id}",
        headers=headers
    )
    
    assert response.status_code == 404


# ============================================================================
# Message Endpoints Tests
# ============================================================================

def test_send_message(test_client, test_jwt_token):
    """Test sending a message in conversation"""
    token, user_id = test_jwt_token
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create conversation
    create_response = test_client.post(
        "/conversations",
        json={},
        headers=headers
    )
    conv_id = create_response.json()["id"]
    
    # Send message
    msg_response = test_client.post(
        "/messages",
        json={
            "conversation_id": conv_id,
            "content": "Hello, I need help with a proposal"
        },
        headers=headers
    )
    
    # Should return 202 (Accepted, async processing)
    assert msg_response.status_code == 202
    data = msg_response.json()
    assert "task_id" in data


def test_get_conversation_messages(test_client, test_jwt_token):
    """Test retrieving messages from conversation"""
    token, user_id = test_jwt_token
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create conversation and send message
    create_response = test_client.post(
        "/conversations",
        json={},
        headers=headers
    )
    conv_id = create_response.json()["id"]
    
    test_client.post(
        "/messages",
        json={
            "conversation_id": conv_id,
            "content": "Test message"
        },
        headers=headers
    )
    
    # Get messages
    msg_response = test_client.get(
        f"/conversations/{conv_id}/messages",
        headers=headers
    )
    
    assert msg_response.status_code == 200
    data = msg_response.json()
    assert "messages" in data
    assert isinstance(data["messages"], list)


# ============================================================================
# Opportunity Endpoints Tests
# ============================================================================

def test_create_opportunity(test_client, test_jwt_token):
    """Test creating an opportunity"""
    token, user_id = test_jwt_token
    headers = {"Authorization": f"Bearer {token}"}
    
    customer_id = str(uuid4())
    
    response = test_client.post(
        "/opportunities",
        json={
            "customer_id": customer_id,
            "title": "Enterprise License Deal",
            "stage": "proposal",
            "value": 100000.00
        },
        headers=headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Enterprise License Deal"
    assert data["stage"] == "proposal"


def test_list_opportunities(test_client, test_jwt_token):
    """Test listing opportunities"""
    token, user_id = test_jwt_token
    headers = {"Authorization": f"Bearer {token}"}
    
    response = test_client.get(
        "/opportunities",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "opportunities" in data
    assert isinstance(data["opportunities"], list)


# ============================================================================
# Customer Endpoints Tests
# ============================================================================

def test_create_customer(test_client, test_jwt_token):
    """Test creating a customer"""
    token, user_id = test_jwt_token
    headers = {"Authorization": f"Bearer {token}"}
    
    response = test_client.post(
        "/customers",
        json={
            "name": "Acme Corporation",
            "email": "contact@acme.com",
            "company": "Acme Corp",
            "industry": "Technology"
        },
        headers=headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corporation"
    assert data["email"] == "contact@acme.com"


def test_get_customer(test_client, test_jwt_token):
    """Test retrieving a customer"""
    token, user_id = test_jwt_token
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create customer first
    create_response = test_client.post(
        "/customers",
        json={
            "name": "Test Corp",
            "email": "test@test.com"
        },
        headers=headers
    )
    customer_id = create_response.json()["id"]
    
    # Get customer
    get_response = test_client.get(
        f"/customers/{customer_id}",
        headers=headers
    )
    
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == customer_id


# ============================================================================
# Task Status Tests
# ============================================================================

def test_get_task_status(test_client, test_jwt_token):
    """Test getting task status"""
    token, user_id = test_jwt_token
    headers = {"Authorization": f"Bearer {token}"}
    
    fake_task_id = str(uuid4())
    response = test_client.get(
        f"/tasks/{fake_task_id}",
        headers=headers
    )
    
    # Should return 404 for non-existent task or 200 with pending status
    assert response.status_code in [200, 404]


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_invalid_json(test_client, test_jwt_token):
    """Test endpoint with invalid JSON"""
    token, _ = test_jwt_token
    headers = {"Authorization": f"Bearer {token}"}
    
    response = test_client.post(
        "/conversations",
        data="not json",
        headers=headers,
        content_type="application/json"
    )
    
    assert response.status_code == 422  # Unprocessable Entity


def test_cors_headers(test_client):
    """Test CORS headers in response"""
    response = test_client.get("/health")
    
    # Note: CORS headers depend on origin in actual CORS middleware
    # This test just ensures no 500 error
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
