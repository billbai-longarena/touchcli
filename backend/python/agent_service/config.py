"""
Configuration management for TouchCLI Agent Service
Environment-based settings for development, staging, and production
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/touchcli"
    )
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    db_pool_timeout: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    db_pool_recycle: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))

    # Redis/Cache
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Celery
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # Server
    agent_service_port: int = int(os.getenv("AGENT_SERVICE_PORT", 8000))
    gateway_port: int = int(os.getenv("GATEWAY_PORT", 8080))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    sql_echo: bool = os.getenv("SQL_ECHO", "false").lower() == "true"

    # Sentry
    sentry_dsn: Optional[str] = os.getenv("SENTRY_DSN")
    sentry_environment: str = os.getenv("SENTRY_ENVIRONMENT", "development")
    sentry_traces_sample_rate: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

    # OpenTelemetry
    otel_enabled: bool = os.getenv("OTEL_ENABLED", "false").lower() == "true"
    otel_exporter_otlp_endpoint: Optional[str] = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    # LangGraph
    langgraph_api_key: Optional[str] = os.getenv("LANGGRAPH_API_KEY")

    # JWT/Auth
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_hours: int = int(os.getenv("JWT_EXPIRATION_HOURS", 1))

    # Feature flags
    debug_mode: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    allow_cors: bool = os.getenv("ALLOW_CORS", "true").lower() == "true"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get global settings instance"""
    return settings
