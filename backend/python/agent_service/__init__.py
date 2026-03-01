"""
TouchCLI Agent Service Package
Phase 2: Backend infrastructure implementation
"""

__version__ = "0.1.0"
__author__ = "TouchCLI Team"

from agent_service.models import Base
from agent_service.db import SessionLocal, get_db, engine

__all__ = [
    "Base",
    "SessionLocal",
    "get_db",
    "engine",
]
