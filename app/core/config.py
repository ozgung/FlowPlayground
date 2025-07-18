"""
Configuration management for FlowPlayground.
"""
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from enum import Enum
import os


class Environment(str, Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "FlowPlayground"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: Environment = Environment.DEVELOPMENT
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    api_key_header: str = "X-API-Key"
    cors_origins: str = "*"
    
    # File Upload
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    upload_dir: str = "uploads"
    allowed_image_types: List[str] = ["image/jpeg", "image/png", "image/webp"]
    allowed_video_types: List[str] = ["video/mp4", "video/avi", "video/mov"]
    
    # External APIs
    fal_ai_api_key: str = Field(..., env="FAL_AI_API_KEY")
    fal_ai_base_url: str = "https://fal.run/fal-ai"
    fal_ai_timeout: int = 300  # 5 minutes
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_expire_time: int = 3600  # 1 hour
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 3600  # 1 hour
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Gradio
    gradio_enabled: bool = True
    gradio_port: int = 7860
    gradio_auth: Optional[tuple] = None
    
    @validator("environment", pre=True)
    def validate_environment(cls, v):
        if isinstance(v, str):
            return Environment(v.lower())
        return v
    
    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @validator("debug", pre=True)
    def validate_debug(cls, v, values):
        if values.get("environment") == Environment.PRODUCTION:
            return False
        return v
    
    @validator("reload", pre=True)
    def validate_reload(cls, v, values):
        if values.get("environment") == Environment.PRODUCTION:
            return False
        return v
    
    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION
    
    @property
    def upload_path(self) -> str:
        return os.path.abspath(self.upload_dir)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()