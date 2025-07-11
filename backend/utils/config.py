"""
Configuration management for the Multi-Agent Negotiation Framework with ADK support
"""

from pydantic import BaseSettings, Field
from typing import Optional, Dict, Any
import os

class Settings(BaseSettings):
    """Application settings with ADK and A2A protocol configuration"""
    
    # Application Settings
    app_name: str = Field(default="Multi-Agent Negotiation Framework", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")
    
    # Database Settings
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # ChromaDB Settings
    chroma_host: str = Field(default="localhost", env="CHROMA_HOST")
    chroma_port: int = Field(default=8001, env="CHROMA_PORT")
    chroma_ssl: bool = Field(default=False, env="CHROMA_SSL")
    
    # Memory Settings
    memory_ttl_seconds: int = Field(default=3600, env="MEMORY_TTL_SECONDS")  # 1 hour
    max_session_history: int = Field(default=1000, env="MAX_SESSION_HISTORY")
    
    # LLM Settings (Legacy - kept for backward compatibility)
    llm_provider: str = Field(default="openai", env="LLM_PROVIDER")
    llm_model_name: str = Field(default="gpt-4", env="LLM_MODEL_NAME")
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=1024, env="LLM_MAX_TOKENS")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Google ADK Settings
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    google_project_id: Optional[str] = Field(default=None, env="GOOGLE_PROJECT_ID")
    google_location: str = Field(default="us-central1", env="GOOGLE_LOCATION")
    use_vertex_ai: bool = Field(default=False, env="GOOGLE_GENAI_USE_VERTEXAI")
    
    # ADK Model Configuration
    adk_model_name: str = Field(default="gemini-2.0-flash", env="ADK_MODEL_NAME")
    adk_model_temperature: float = Field(default=0.7, env="ADK_MODEL_TEMPERATURE")
    adk_model_max_tokens: int = Field(default=2048, env="ADK_MODEL_MAX_TOKENS")
    adk_model_top_p: float = Field(default=0.9, env="ADK_MODEL_TOP_P")
    adk_model_top_k: int = Field(default=40, env="ADK_MODEL_TOP_K")
    
    # ADK Orchestrator Settings
    adk_orchestrator_enabled: bool = Field(default=True, env="ADK_ORCHESTRATOR_ENABLED")
    adk_orchestrator_max_agents: int = Field(default=10, env="ADK_ORCHESTRATOR_MAX_AGENTS")
    adk_orchestrator_timeout: int = Field(default=300, env="ADK_ORCHESTRATOR_TIMEOUT")  # 5 minutes
    adk_orchestrator_retry_attempts: int = Field(default=3, env="ADK_ORCHESTRATOR_RETRY_ATTEMPTS")
    adk_orchestrator_parallel_execution: bool = Field(default=False, env="ADK_ORCHESTRATOR_PARALLEL_EXECUTION")
    
    # ADK Agent Settings
    adk_agent_timeout: int = Field(default=60, env="ADK_AGENT_TIMEOUT")  # 1 minute
    adk_agent_max_retries: int = Field(default=3, env="ADK_AGENT_MAX_RETRIES")
    adk_agent_memory_enabled: bool = Field(default=True, env="ADK_AGENT_MEMORY_ENABLED")
    adk_agent_tools_enabled: bool = Field(default=True, env="ADK_AGENT_TOOLS_ENABLED")
    adk_agent_context_window: int = Field(default=5, env="ADK_AGENT_CONTEXT_WINDOW")  # Last N messages
    
    # Google A2A Protocol Configuration
    a2a_protocol_version: str = Field(default="1.0", env="A2A_PROTOCOL_VERSION")
    a2a_message_timeout: int = Field(default=30, env="A2A_MESSAGE_TIMEOUT")
    a2a_max_message_size: int = Field(default=10240, env="A2A_MAX_MESSAGE_SIZE")  # 10KB
    a2a_enable_encryption: bool = Field(default=False, env="A2A_ENABLE_ENCRYPTION")
    a2a_enable_compression: bool = Field(default=True, env="A2A_ENABLE_COMPRESSION")
    a2a_retry_attempts: int = Field(default=3, env="A2A_RETRY_ATTEMPTS")
    a2a_batch_processing: bool = Field(default=False, env="A2A_BATCH_PROCESSING")
    
    # Debate Engine Settings
    debate_max_rounds: int = Field(default=10, env="DEBATE_MAX_ROUNDS")
    debate_min_agents: int = Field(default=3, env="DEBATE_MIN_AGENTS")
    debate_max_agents: int = Field(default=10, env="DEBATE_MAX_AGENTS")
    debate_consensus_threshold: float = Field(default=0.7, env="DEBATE_CONSENSUS_THRESHOLD")
    debate_turn_timeout: int = Field(default=120, env="DEBATE_TURN_TIMEOUT")  # 2 minutes
    debate_auto_consensus_check: bool = Field(default=True, env="DEBATE_AUTO_CONSENSUS_CHECK")
    
    # Consensus Settings
    consensus_method: str = Field(default="simple_majority", env="CONSENSUS_METHOD")  # simple_majority, borda_count, delphi
    consensus_min_agreement: float = Field(default=0.6, env="CONSENSUS_MIN_AGREEMENT")
    consensus_max_iterations: int = Field(default=5, env="CONSENSUS_MAX_ITERATIONS")
    consensus_timeout: int = Field(default=60, env="CONSENSUS_TIMEOUT")
    
    # WebSocket Settings
    websocket_heartbeat: int = Field(default=30, env="WEBSOCKET_HEARTBEAT")
    websocket_max_connections: int = Field(default=100, env="WEBSOCKET_MAX_CONNECTIONS")
    websocket_message_queue_size: int = Field(default=1000, env="WEBSOCKET_MESSAGE_QUEUE_SIZE")
    
    # Logging Settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    enable_request_logging: bool = Field(default=True, env="ENABLE_REQUEST_LOGGING")
    
    # Security Settings
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    enable_rate_limiting: bool = Field(default=True, env="ENABLE_RATE_LIMITING")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    # Monitoring and Observability
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8001, env="METRICS_PORT")
    enable_tracing: bool = Field(default=False, env="ENABLE_TRACING")
    tracing_endpoint: Optional[str] = Field(default=None, env="TRACING_ENDPOINT")
    
    # ADK Observability Settings
    adk_enable_telemetry: bool = Field(default=True, env="ADK_ENABLE_TELEMETRY")
    adk_telemetry_endpoint: Optional[str] = Field(default=None, env="ADK_TELEMETRY_ENDPOINT")
    adk_trace_agent_interactions: bool = Field(default=True, env="ADK_TRACE_AGENT_INTERACTIONS")
    adk_trace_a2a_messages: bool = Field(default=True, env="ADK_TRACE_A2A_MESSAGES")
    
    # Development Settings
    auto_reload: bool = Field(default=False, env="AUTO_RELOAD")
    mock_llm_responses: bool = Field(default=False, env="MOCK_LLM_RESPONSES")
    enable_debug_endpoints: bool = Field(default=False, env="ENABLE_DEBUG_ENDPOINTS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_adk_model_config(self) -> Dict[str, Any]:
        """Get ADK model configuration as a dictionary"""
        return {
            "model_name": self.adk_model_name,
            "temperature": self.adk_model_temperature,
            "max_tokens": self.adk_model_max_tokens,
            "top_p": self.adk_model_top_p,
            "top_k": self.adk_model_top_k,
            "api_key": self.google_api_key,
            "project_id": self.google_project_id,
            "location": self.google_location,
            "use_vertex_ai": self.use_vertex_ai,
        }
    
    def get_adk_orchestrator_config(self) -> Dict[str, Any]:
        """Get ADK orchestrator configuration as a dictionary"""
        return {
            "enabled": self.adk_orchestrator_enabled,
            "max_agents": self.adk_orchestrator_max_agents,
            "timeout": self.adk_orchestrator_timeout,
            "retry_attempts": self.adk_orchestrator_retry_attempts,
            "parallel_execution": self.adk_orchestrator_parallel_execution,
        }
    
    def get_a2a_protocol_config(self) -> Dict[str, Any]:
        """Get A2A protocol configuration as a dictionary"""
        return {
            "version": self.a2a_protocol_version,
            "message_timeout": self.a2a_message_timeout,
            "max_message_size": self.a2a_max_message_size,
            "enable_encryption": self.a2a_enable_encryption,
            "enable_compression": self.a2a_enable_compression,
            "retry_attempts": self.a2a_retry_attempts,
            "batch_processing": self.a2a_batch_processing,
        }
    
    def get_debate_config(self) -> Dict[str, Any]:
        """Get debate engine configuration as a dictionary"""
        return {
            "max_rounds": self.debate_max_rounds,
            "min_agents": self.debate_min_agents,
            "max_agents": self.debate_max_agents,
            "consensus_threshold": self.debate_consensus_threshold,
            "turn_timeout": self.debate_turn_timeout,
            "auto_consensus_check": self.debate_auto_consensus_check,
        }
    
    def get_consensus_config(self) -> Dict[str, Any]:
        """Get consensus evaluation configuration as a dictionary"""
        return {
            "method": self.consensus_method,
            "min_agreement": self.consensus_min_agreement,
            "max_iterations": self.consensus_max_iterations,
            "timeout": self.consensus_timeout,
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"
    
    def validate_adk_config(self) -> bool:
        """Validate ADK configuration"""
        if not self.google_api_key and not (self.google_project_id and self.use_vertex_ai):
            return False
        
        if self.adk_model_temperature < 0 or self.adk_model_temperature > 2:
            return False
        
        if self.adk_model_max_tokens < 1:
            return False
        
        return True

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get application settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def reload_settings() -> Settings:
    """Reload settings from environment"""
    global _settings
    _settings = Settings()
    return _settings 