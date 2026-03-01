"""
JWT Authentication utilities for FastAPI
Handles token generation, validation, and dependency injection
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

# Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "1"))

security = HTTPBearer()


def create_token(user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate a JWT token for a user.

    Args:
        user_id: User UUID
        expires_delta: Optional custom expiration time

    Returns:
        JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)

    expire = datetime.utcnow() + expires_delta
    payload = {
        "user_id": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str) -> UUID:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        User UUID extracted from token

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return UUID(user_id)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user_id in token",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> UUID:
    """
    FastAPI dependency to extract and validate the current user from JWT token.

    Usage in endpoints:
        @app.post("/protected")
        async def protected_endpoint(user_id: UUID = Depends(get_current_user)):
            ...

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        Authenticated user UUID

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials
    return verify_token(token)
