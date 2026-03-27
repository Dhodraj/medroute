import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Model Configuration
    model_backend: str = Field(default="ollama", env="MODEL_BACKEND")
    ollama_model: str = Field(default="medllama2:7b", env="OLLAMA_MODEL")
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./triage.db", env="DATABASE_URL")
    
    # Application Configuration
    app_name: str = "Healthcare Triage Backend"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # Request limits
    max_query_length: int = Field(default=2000, env="MAX_QUERY_LENGTH")
    request_timeout_seconds: int = Field(default=30, env="REQUEST_TIMEOUT_SECONDS")
    
    # Cleanup Configuration
    log_retention_days: int = Field(default=30, env="LOG_RETENTION_DAYS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        protected_namespaces = ()


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def reload_settings():
    """Reload settings from environment"""
    global settings
    settings = Settings()
    return settings
