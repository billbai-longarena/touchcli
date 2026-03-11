"""
Pytest configuration and fixtures
"""

import pytest
import sys
from pathlib import Path
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# ---------------------------------------------------------------------------
# Shared in-memory SQLite engine (StaticPool: all connections share one DB)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite:///:memory:"

_test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Patch the app's db module BEFORE importing main so startup uses the same DB
import agent_service.db as _app_db  # noqa: E402

_app_db.engine = _test_engine
_app_db.SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=_test_engine
)

# Now import models and create all tables on the shared test engine
from agent_service.models import Base, User  # noqa: E402

Base.metadata.create_all(bind=_test_engine)


@pytest.fixture(scope="session")
def test_db_engine():
    """Shared test database engine (SQLite in-memory, StaticPool)."""
    yield _test_engine
    Base.metadata.drop_all(bind=_test_engine)


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
    db.rollback()
    db.close()


@pytest.fixture
def test_jwt_token(test_db_session):
    """Generate test JWT token and create corresponding User in DB."""
    from agent_service.auth import create_token

    user_id = uuid4()

    # Pre-create the user so create_conversation auth check passes
    user = User(
        id=user_id,
        email=f"{user_id}@test.com",
        name="Test User",
        role="salesperson",
    )
    test_db_session.add(user)
    test_db_session.commit()

    token = create_token(user_id)
    return token, user_id


@pytest.fixture
def test_client(test_db_session):
    """Create test client with dependency override."""
    from agent_service.main import app
    from agent_service.db import get_db

    def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    from fastapi.testclient import TestClient

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()
