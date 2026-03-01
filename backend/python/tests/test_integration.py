"""
Integration tests for TouchCLI Agent Service.
Tests the complete message flow: conversation creation → message sending → agent response.
"""

import pytest
import os
from uuid import uuid4
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

try:
    from agent_service.main import app
    from agent_service.models import Base, User, Customer, Opportunity
    from agent_service.db import get_db
    from agent_service.auth import create_token
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent_service.main import app
    from agent_service.models import Base, User, Customer, Opportunity
    from agent_service.db import get_db
    from agent_service.auth import create_token


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_db():
    """Create in-memory test database."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


@pytest.fixture
def db_session(test_db):
    """Provide a database session for each test."""
    yield test_db
    test_db.rollback()


@pytest.fixture
def client(db_session):
    """Create test client with mocked database."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        id=uuid4(),
        name="Test User",
        email="test@example.com",
        role="salesperson",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_customer(db_session):
    """Create a test customer."""
    customer = Customer(
        id=uuid4(),
        name="Test Customer",
        customer_type="company",
        industry="Technology",
        email="customer@example.com",
        phone="+1-555-0100",
        company_size="100-500",
        website="https://example.com"
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def test_opportunity(db_session, test_customer):
    """Create a test opportunity."""
    opportunity = Opportunity(
        id=uuid4(),
        customer_id=test_customer.id,
        name="Test Deal",
        description="Test opportunity",
        amount=50000.00,
        currency="USD",
        status="discovery",
        probability=0.5,
        expected_close_date=datetime.utcnow() + timedelta(days=30)
    )
    db_session.add(opportunity)
    db_session.commit()
    db_session.refresh(opportunity)
    return opportunity


@pytest.fixture
def auth_token(test_user):
    """Generate JWT token for test user."""
    return create_token(test_user.id)


@pytest.fixture
def auth_headers(auth_token):
    """Create Authorization headers with JWT token."""
    return {"Authorization": f"Bearer {auth_token}"}


# ============================================================================
# Health Check Tests
# ============================================================================

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded", "unhealthy"]
    assert "timestamp" in data
    assert "version" in data
    assert "checks" in data


# ============================================================================
# Authentication Tests
# ============================================================================

def test_login_success(client, test_user):
    """Test successful token generation."""
    response = client.post(f"/login?user_id={test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert str(data["user_id"]) == str(test_user.id)


def test_login_user_not_found(client):
    """Test login with non-existent user."""
    fake_uuid = uuid4()
    response = client.post(f"/login?user_id={fake_uuid}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ============================================================================
# Conversation Tests
# ============================================================================

def test_create_conversation_success(client, auth_headers, test_customer):
    """Test successful conversation creation."""
    response = client.post(
        "/conversations",
        json={
            "customer_id": str(test_customer.id),
            "opportunity_id": None,
            "mode": "sales"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert str(data["customer_id"]) == str(test_customer.id)
    assert data["mode"] == "sales"


def test_create_conversation_missing_auth(client, test_customer):
    """Test conversation creation without authentication."""
    response = client.post(
        "/conversations",
        json={
            "customer_id": str(test_customer.id),
            "opportunity_id": None,
            "mode": "sales"
        }
    )
    assert response.status_code == 403  # Forbidden (missing auth)


def test_create_conversation_invalid_token(client, test_customer):
    """Test conversation creation with invalid token."""
    response = client.post(
        "/conversations",
        json={
            "customer_id": str(test_customer.id),
            "opportunity_id": None,
            "mode": "sales"
        },
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401  # Unauthorized


def test_get_conversation(client, auth_headers, test_user, test_customer):
    """Test fetching conversation metadata."""
    # First create a conversation
    create_response = client.post(
        "/conversations",
        json={
            "customer_id": str(test_customer.id),
            "opportunity_id": None,
            "mode": "sales"
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201
    conversation_id = create_response.json()["id"]

    # Then fetch it
    response = client.get(f"/conversations/{conversation_id}")
    assert response.status_code == 200
    data = response.json()
    assert str(data["id"]) == conversation_id
    assert str(data["customer_id"]) == str(test_customer.id)


def test_get_conversation_not_found(client):
    """Test fetching non-existent conversation."""
    fake_uuid = uuid4()
    response = client.get(f"/conversations/{fake_uuid}")
    assert response.status_code == 404


# ============================================================================
# Message Tests
# ============================================================================

def test_send_message_success(client, auth_headers, test_user, test_customer):
    """Test successful message sending and agent processing."""
    # Create conversation first
    conv_response = client.post(
        "/conversations",
        json={
            "customer_id": str(test_customer.id),
            "opportunity_id": None,
            "mode": "sales"
        },
        headers=auth_headers
    )
    conversation_id = conv_response.json()["id"]

    # Send message
    response = client.post(
        "/messages",
        json={
            "conversation_id": conversation_id,
            "content": "Tell me about your products",
            "content_type": "text",
            "attachments": []
        },
        headers=auth_headers
    )
    assert response.status_code == 202  # Accepted (async)
    data = response.json()
    assert "message_id" in data
    assert "task_id" in data
    assert "agent_response" in data


def test_send_message_missing_conversation(client, auth_headers):
    """Test sending message to non-existent conversation."""
    fake_conv_id = uuid4()
    response = client.post(
        "/messages",
        json={
            "conversation_id": str(fake_conv_id),
            "content": "Hello",
            "content_type": "text",
            "attachments": []
        },
        headers=auth_headers
    )
    assert response.status_code == 404


def test_send_message_without_auth(client, test_customer):
    """Test message sending without authentication."""
    conv_id = uuid4()
    response = client.post(
        "/messages",
        json={
            "conversation_id": str(conv_id),
            "content": "Hello",
            "content_type": "text",
            "attachments": []
        }
    )
    assert response.status_code == 403  # Forbidden (missing auth)


def test_get_conversation_messages(client, auth_headers, test_customer):
    """Test fetching message history."""
    # Create conversation
    conv_response = client.post(
        "/conversations",
        json={
            "customer_id": str(test_customer.id),
            "opportunity_id": None,
            "mode": "sales"
        },
        headers=auth_headers
    )
    conversation_id = conv_response.json()["id"]

    # Send messages
    for i in range(3):
        client.post(
            "/messages",
            json={
                "conversation_id": conversation_id,
                "content": f"Message {i}",
                "content_type": "text",
                "attachments": []
            },
            headers=auth_headers
        )

    # Fetch history
    response = client.get(f"/conversations/{conversation_id}/messages")
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert "total" in data
    assert data["total"] >= 3  # At least our sent messages


# ============================================================================
# Customer Tests
# ============================================================================

def test_create_customer(client, test_customer):
    """Test creating a customer."""
    response = client.post(
        "/customers",
        json={
            "name": "New Customer",
            "customer_type": "individual",
            "industry": "Finance",
            "email": "new@example.com",
            "phone": "+1-555-0200",
            "company_size": None,
            "website": None
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Customer"


def test_get_customer(client, test_customer):
    """Test fetching customer."""
    response = client.get(f"/customers/{test_customer.id}")
    assert response.status_code == 200
    data = response.json()
    assert str(data["id"]) == str(test_customer.id)
    assert data["name"] == test_customer.name


def test_get_customer_not_found(client):
    """Test fetching non-existent customer."""
    fake_uuid = uuid4()
    response = client.get(f"/customers/{fake_uuid}")
    assert response.status_code == 404


# ============================================================================
# Opportunity Tests
# ============================================================================

def test_create_opportunity(client, test_customer):
    """Test creating an opportunity."""
    response = client.post(
        "/opportunities",
        json={
            "customer_id": str(test_customer.id),
            "name": "New Deal",
            "description": "Test opportunity",
            "amount": 100000,
            "currency": "USD",
            "status": "discovery",
            "probability": 0.3,
            "expected_close_date": "2026-04-02",
            "metadata": {}
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Deal"
    assert data["amount"] == 100000


def test_create_opportunity_missing_customer(client):
    """Test creating opportunity with non-existent customer."""
    fake_uuid = uuid4()
    response = client.post(
        "/opportunities",
        json={
            "customer_id": str(fake_uuid),
            "name": "New Deal",
            "description": "Test",
            "amount": 50000,
            "currency": "USD",
            "status": "discovery",
            "probability": 0.5,
            "expected_close_date": "2026-04-02",
            "metadata": {}
        }
    )
    assert response.status_code == 404


def test_list_opportunities(client, test_customer, test_opportunity):
    """Test listing opportunities with filters."""
    response = client.get("/opportunities")
    assert response.status_code == 200
    data = response.json()
    assert "opportunities" in data
    assert "total" in data

    # Filter by customer
    response = client.get(f"/opportunities?customer_id={test_customer.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


# ============================================================================
# Task Status Tests
# ============================================================================

def test_get_task_status(client, auth_headers, test_customer):
    """Test polling task status."""
    # Send message to create a task
    conv_response = client.post(
        "/conversations",
        json={
            "customer_id": str(test_customer.id),
            "opportunity_id": None,
            "mode": "sales"
        },
        headers=auth_headers
    )
    conversation_id = conv_response.json()["id"]

    msg_response = client.post(
        "/messages",
        json={
            "conversation_id": conversation_id,
            "content": "Test",
            "content_type": "text",
            "attachments": []
        },
        headers=auth_headers
    )
    task_id = msg_response.json()["task_id"]

    # Poll status
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "status" in data


# ============================================================================
# End-to-End Flow Test
# ============================================================================

def test_complete_message_flow(client, auth_headers, test_user, test_customer, test_opportunity):
    """
    Complete end-to-end test: create conversation → send messages → fetch history.
    """
    # 1. Create conversation
    conv_response = client.post(
        "/conversations",
        json={
            "customer_id": str(test_customer.id),
            "opportunity_id": str(test_opportunity.id),
            "mode": "sales"
        },
        headers=auth_headers
    )
    assert conv_response.status_code == 201
    conversation_id = conv_response.json()["id"]
    assert conversation_id

    # 2. Send user message
    msg_response = client.post(
        "/messages",
        json={
            "conversation_id": conversation_id,
            "content": "What are your best solutions for our company?",
            "content_type": "text",
            "attachments": []
        },
        headers=auth_headers
    )
    assert msg_response.status_code == 202
    data = msg_response.json()
    assert data["agent_response"]

    # 3. Fetch conversation history
    history_response = client.get(f"/conversations/{conversation_id}/messages")
    assert history_response.status_code == 200
    history = history_response.json()
    assert history["total"] >= 1

    # 4. Verify conversation exists
    conv_check = client.get(f"/conversations/{conversation_id}")
    assert conv_check.status_code == 200
    assert str(conv_check.json()["customer_id"]) == str(test_customer.id)
