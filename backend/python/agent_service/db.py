"""
Database connection and session management for TouchCLI
SQLAlchemy configuration with connection pooling and session lifecycle
"""

import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/touchcli"
)

# Connection pool configuration
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

# ============================================================================
# Engine Configuration
# ============================================================================

engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "False").lower() == "true",
    poolclass=QueuePool,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    pool_pre_ping=True,  # Verify connections before use
    connect_args={
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000",  # 30 second query timeout
    }
)


# ============================================================================
# Event Handlers for Connection Management
# ============================================================================

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set PostgreSQL connection parameters"""
    if DATABASE_URL.startswith("postgresql"):
        # Enable connection logging
        logger.debug("Database connection established")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checkout"""
    logger.debug(f"Connection checked out from pool")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log connection checkin"""
    logger.debug(f"Connection returned to pool")


# ============================================================================
# Session Factory
# ============================================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


# ============================================================================
# Database Dependency for FastAPI
# ============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session injection.

    Yields:
        SQLAlchemy Session for the request

    Example:
        @app.get("/users/{user_id}")
        async def get_user(user_id: str, db: Session = Depends(get_db)):
            return db.query(User).filter(User.id == user_id).first()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()


# ============================================================================
# Database Utilities
# ============================================================================

def init_db():
    """
    Initialize database with tables from models.

    Call this once on application startup:
        from agent_service.db import init_db, engine
        from agent_service.models import Base
        init_db()
    """
    from agent_service.models import Base

    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_db():
    """
    Drop all database tables.

    WARNING: This deletes all data. Use only in development!
    """
    from agent_service.models import Base

    logger.warning("DROPPING ALL TABLES - THIS IS DESTRUCTIVE!")
    Base.metadata.drop_all(bind=engine)
    logger.warning("All tables dropped")


async def get_db_health() -> dict:
    """
    Check database health status.

    Returns:
        dict with status, latency_ms, and last_checked timestamp
    """
    import time
    from datetime import datetime

    try:
        start = time.time()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency = int((time.time() - start) * 1000)

        return {
            "status": "ok" if latency < 100 else "degraded" if latency < 500 else "error",
            "latency_ms": latency,
            "last_checked": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error",
            "latency_ms": None,
            "last_checked": datetime.utcnow().isoformat() + "Z",
            "error": str(e)
        }


def get_connection_pool_status() -> dict:
    """
    Get connection pool statistics.

    Returns:
        dict with pool size, overflow, checked_out connections
    """
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total": pool.size() + pool.overflow()
    }


# ============================================================================
# Transaction Context Manager
# ============================================================================

class TransactionManager:
    """Context manager for database transactions"""

    def __init__(self, db: Session):
        self.db = db

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.db.rollback()
            logger.error(f"Transaction rolled back due to: {exc_val}")
        else:
            self.db.commit()
        self.db.close()


def transaction(db: Session) -> TransactionManager:
    """
    Create a transaction context manager.

    Example:
        with transaction(db) as session:
            user = User(email="user@example.com")
            session.add(user)
            # Auto-commits on success, auto-rollbacks on error
    """
    return TransactionManager(db)


# ============================================================================
# Query Helpers
# ============================================================================

class QueryHelper:
    """Helper methods for common queries"""

    @staticmethod
    def paginate(query, offset: int = 0, limit: int = 50):
        """
        Paginate query results.

        Args:
            query: SQLAlchemy query object
            offset: Number of records to skip
            limit: Maximum number of records to return (max 500)

        Returns:
            Tuple of (total_count, results)
        """
        limit = min(limit, 500)  # Cap at 500
        total = query.count()
        results = query.offset(offset).limit(limit).all()
        return total, results

    @staticmethod
    def get_or_raise(query, entity_name: str):
        """
        Get single result or raise 404.

        Args:
            query: SQLAlchemy query returning single record
            entity_name: Name of entity for error message

        Returns:
            Single result

        Raises:
            Exception: If not found (caller should convert to 404)
        """
        result = query.first()
        if not result:
            raise ValueError(f"{entity_name} not found")
        return result
