"""
Configuration management for TouchCLI Agent Service
"""

import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:  # pragma: no cover - fallback for minimal local runtime
    BaseSettings = object  # type: ignore[assignment]


def _as_bool(value: str, default: bool = False) -> bool:
    raw = (value or "").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return default


class Settings(BaseSettings):
    """Application configuration from environment variables"""

    # Database
    database_url: str = "postgresql://localhost:5432/touchcli"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # LangGraph & AI
    langgraph_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Server
    agent_service_host: str = "0.0.0.0"
    agent_service_port: int = 8000
    gateway_host: str = "0.0.0.0"
    gateway_port: int = 8080

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    log_file: Optional[str] = None

    # Environment
    debug: bool = False
    environment: str = "development"  # development, staging, production

    if BaseSettings is not object:
        class Config:
            env_file = ".env"
            case_sensitive = False

    def __init__(self):
        # pydantic-settings path: let BaseSettings handle env resolution.
        if BaseSettings is not object:
            super().__init__()
            return

        # Fallback path: lightweight env mapping to avoid hard crash when
        # pydantic-settings is unavailable in local runtime.
        self.database_url = os.getenv("DATABASE_URL", self.database_url)
        self.redis_url = os.getenv("REDIS_URL", self.redis_url)
        self.celery_broker_url = os.getenv("CELERY_BROKER_URL", self.celery_broker_url)
        self.celery_result_backend = os.getenv("CELERY_RESULT_BACKEND", self.celery_result_backend)
        self.langgraph_api_key = os.getenv("LANGGRAPH_API_KEY", self.langgraph_api_key)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.agent_service_host = os.getenv("AGENT_SERVICE_HOST", self.agent_service_host)
        self.agent_service_port = int(os.getenv("AGENT_SERVICE_PORT", str(self.agent_service_port)))
        self.gateway_host = os.getenv("GATEWAY_HOST", self.gateway_host)
        self.gateway_port = int(os.getenv("GATEWAY_PORT", str(self.gateway_port)))
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        self.log_format = os.getenv("LOG_FORMAT", self.log_format)
        self.log_file = os.getenv("LOG_FILE", self.log_file) or None
        self.debug = _as_bool(os.getenv("DEBUG_MODE", str(self.debug)), self.debug)
        self.environment = os.getenv("ENVIRONMENT", self.environment)


settings = Settings()
