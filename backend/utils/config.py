"""
Configuration management for the Multi-Agent Negotiation Framework
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    app_name: str = "Multi-Agent Negotiation Framework"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # ChromaDB Configuration
    chroma_host: str = Field(default="localhost", env="CHROMA_HOST")
    chroma_port: int = Field(default=8000, env="CHROMA_PORT")
    chroma_persist_directory: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    
    # Debate Configuration
    default_agent_count: int = Field(default=5, env="DEFAULT_AGENT_COUNT")
    max_debate_rounds: int = Field(default=10, env="MAX_DEBATE_ROUNDS")
    consensus_threshold: float = Field(default=0.8, env="CONSENSUS_THRESHOLD")
    debate_timeout_seconds: int = Field(default=300, env="DEBATE_TIMEOUT_SECONDS")
    
    # Memory Configuration
    max_memory_size: int = Field(default=1000, env="MAX_MEMORY_SIZE")
    memory_ttl_seconds: int = Field(default=3600, env="MEMORY_TTL_SECONDS")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # CORS Configuration
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    # WebSocket Configuration
    websocket_ping_interval: int = Field(default=20, env="WEBSOCKET_PING_INTERVAL")
    websocket_ping_timeout: int = Field(default=20, env="WEBSOCKET_PING_TIMEOUT")
    
    # Agent Configuration
    agent_generation_timeout: int = Field(default=30, env="AGENT_GENERATION_TIMEOUT")
    agent_reasoning_timeout: int = Field(default=60, env="AGENT_REASONING_TIMEOUT")
    
    # Google A2A Protocol Configuration
    a2a_protocol_version: str = Field(default="1.0", env="A2A_PROTOCOL_VERSION")
    a2a_message_timeout: int = Field(default=30, env="A2A_MESSAGE_TIMEOUT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get the global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def reload_settings() -> Settings:
    """Reload settings from environment"""
    global _settings
    _settings = Settings()
    return _settings

# Environment-specific configurations
def get_development_settings() -> Settings:
    """Get development-specific settings"""
    os.environ.setdefault("DEBUG", "True")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")
    return get_settings()

def get_production_settings() -> Settings:
    """Get production-specific settings"""
    os.environ.setdefault("DEBUG", "False")
    os.environ.setdefault("LOG_LEVEL", "WARNING")
    return get_settings()

def get_test_settings() -> Settings:
    """Get test-specific settings"""
    os.environ.setdefault("DEBUG", "True")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")
    os.environ.setdefault("REDIS_DB", "1")  # Use different Redis DB for tests
    return get_settings() 