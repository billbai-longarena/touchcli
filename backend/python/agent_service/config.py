"""
Configuration management for TouchCLI Agent Service
"""

from pydantic_settings import BaseSettings
from typing import Optional


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

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
