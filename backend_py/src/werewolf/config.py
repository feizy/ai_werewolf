"""Configuration management for werewolf backend."""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Database Configuration
    database_url: str = "postgresql://user:password@localhost:5432/werewolf_db"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_pool_size: int = 10

    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"

    # Anthropic Configuration
    anthropic_api_key: Optional[str] = None

    # WebSocket Configuration
    websocket_cors_origins: str = "http://localhost:3000,http://localhost:3001"
    websocket_ping_timeout: int = 60
    websocket_ping_interval: int = 25

    # Game Configuration
    default_max_players: int = 9
    game_timeout_minutes: int = 30
    min_players_to_start: int = 4

    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/werewolf_backend.log"
    log_rotation: str = "10 MB"
    log_retention: str = "7 days"

    # Security Configuration
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # Performance Configuration
    max_workers: int = 4
    keep_alive: int = 2
    request_timeout: int = 30

    # Development/Testing
    enable_metrics: bool = True
    enable_profiling: bool = False

    @validator("websocket_cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("debug", pre=True)
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v

    
    @validator("enable_metrics", pre=True)
    def parse_enable_metrics(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v

    @validator("enable_profiling", pre=True)
    def parse_enable_profiling(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.debug

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug

    @property
    def websocket_cors_origins_list(self) -> List[str]:
        """Get CORS origins as list."""
        if isinstance(self.websocket_cors_origins, str):
            return [origin.strip() for origin in self.websocket_cors_origins.split(",")]
        return self.websocket_cors_origins or []

    @property
    def agentscope_available(self) -> bool:
        """Check if AgentScope is properly configured."""
        return bool(self.agentscope_api_key)

    @property
    def openai_available(self) -> bool:
        """Check if OpenAI is properly configured."""
        return bool(self.openai_api_key)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()