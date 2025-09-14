"""
Core configuration settings for the OpenSource Sensei backend application.
"""
from typing import Optional, List, Any
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = "OpenSource Sensei API"
    app_version: str = "1.0.0"
    debug: bool = False
    api_prefix: str = "/api/v1"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # MongoDB settings
    mongodb_uri: str = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_database: str = os.environ.get("MONGODB_DATABASE", "opensourcesensei")
    # Persistence control: allow explicit in-memory mode for fast dev
    persistence_mode: str = os.environ.get("PERSISTENCE_MODE", "database")  # 'database' | 'memory'
    disable_database: bool = os.environ.get("DISABLE_DATABASE", "false").lower() in {"1", "true", "yes"}
    
    # Redis settings
    redis_url: str = "redis://localhost:6379/0"
    
    # Celery settings
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # OpenAI settings
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 4000
    
    # GitHub settings
    github_token: Optional[str] = None
    github_api_key: Optional[str] = None
    
    # StackOverflow settings
    stackoverflow_api_key: Optional[str] = None
    
    # Google Custom Search settings
    google_cse_api_key: Optional[str] = None
    google_cse_id: Optional[str] = None
    
    # MongoDB base URI (from .env for reference, but we use mongodb_uri)
    mongodb_base_uri: Optional[str] = None
    
    # File storage settings
    storage_path: str = "./storage"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_types: List[str] = [".zip", ".tar.gz", ".tar", ".rar", ".7z", ".py", ".js", ".ts", ".java", ".cpp", ".c"]
    
    # Analysis settings
    max_concurrent_analyses: int = 5
    analysis_timeout: int = 3600  # 1 hour
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # CORS settings
    # Include common frontend dev ports (React CRA:3000, Vue:8080, Vite:5173) - can be overridden via env CORS_ORIGINS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080", "http://localhost:5173"]
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Agent settings
    agent_pool_size: int = 10
    agent_timeout: int = 300  # 5 minutes
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator('allowed_file_types', mode='before')
    @classmethod
    def parse_allowed_file_types(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    model_config = {
        'env_file': '.env',
        'env_file_encoding': 'utf-8',
        'case_sensitive': False
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings."""
    debug: bool = True
    database_echo: bool = True
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    """Production environment settings."""
    debug: bool = False
    database_echo: bool = False
    log_level: str = "INFO"


class TestSettings(Settings):
    """Test environment settings."""
    database_url: str = "sqlite:///./test.db"
    redis_url: str = "redis://localhost:6379/15"
    celery_broker_url: str = "redis://localhost:6379/14"
    celery_result_backend: str = "redis://localhost:6379/13"


def get_settings_for_environment(env: Optional[str] = None) -> Settings:
    """Get settings for specific environment."""
    if env is None:
        env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()