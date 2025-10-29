"""
Enhanced Settings with Secure Configuration Management
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from api.config.secure_config_manager import get_config_manager, initialize_secure_configuration
from api.utils.logger import get_system_logger

logger = get_system_logger("settings")


class EnhancedSettings(BaseModel):
    """Enhanced application settings with security features"""
    
    # Basic app settings
    app_name: str = Field(default="Whisper Transcriber")
    version: str = Field(default="1.0.0")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    
    # Server settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8001)
    
    # Database settings
    database_url: str = Field(default="sqlite:///./whisper_dev.db")
    db_url: str = Field(default="sqlite:///./whisper_dev.db")  # Alias for compatibility
    
    # Backend settings
    job_queue_backend: str = Field(default="thread")
    storage_backend: str = Field(default="local")
    
    # Development server settings
    vite_api_host: str = Field(default="localhost:8001")
    
    # Security settings - loaded from secure config manager
    secret_key: str = Field(default="")
    jwt_secret_key: str = Field(default="")
    database_encryption_key: str = Field(default="")
    session_secret: str = Field(default="")
    csrf_secret: str = Field(default="")
    
    allowed_hosts: List[str] = Field(default=["*"])
    cors_origins: str = Field(default="*")
    
    # Authentication settings
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    allow_registration: bool = Field(default=True)
    
    # File upload settings
    max_file_size: int = Field(default=100 * 1024 * 1024)  # 100MB
    max_filename_length: int = Field(default=255)
    upload_timeout: int = Field(default=300)  # 5 minutes
    allowed_file_types: List[str] = Field(
        default=["audio/wav", "audio/mp3", "audio/m4a", "audio/flac"]
    )
    
    # Whisper settings
    default_model: str = Field(default="small")
    available_models: List[str] = Field(
        default=["tiny", "small", "medium", "large", "large-v2", "large-v3"]
    )
    
    # Storage paths
    upload_dir: Path = Field(default=Path("uploads"))
    transcripts_dir: Path = Field(default=Path("transcripts"))
    models_dir: Path = Field(default=Path("models"))
    cache_dir: Path = Field(default=Path("cache"))
    
    # Redis/Celery settings (optional)
    redis_url: Optional[str] = Field(default=None)
    celery_broker_url: Optional[str] = Field(default=None)
    
    # Logging settings
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="standard")
    
    # Security hardening settings
    hsts_max_age: int = Field(default=31536000)  # 1 year
    csp_enabled: bool = Field(default=True)
    security_headers_enabled: bool = Field(default=True)
    rate_limit_enabled: bool = Field(default=True)
    
    # Session security
    session_timeout: int = Field(default=3600)  # 1 hour
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @validator("environment")
    def validate_environment(cls, v):
        valid_environments = ["development", "staging", "production", "test"]
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of {valid_environments}")
        return v
    
    @validator("debug")
    def validate_debug_in_production(cls, v, values):
        if values.get("environment") == "production" and v:
            raise ValueError("Debug mode must be disabled in production")
        return v
    
    @validator("secret_key")
    def validate_secret_key_strength(cls, v, values):
        environment = values.get("environment", "development")
        
        if environment == "production":
            if not v or len(v) < 32:
                raise ValueError("Production secret key must be at least 32 characters")
            
            # Check for common weak patterns
            weak_patterns = ["dev", "test", "change", "production", "secret", "admin"]
            v_lower = v.lower()
            for pattern in weak_patterns:
                if pattern in v_lower:
                    raise ValueError(f"Secret key contains weak pattern: {pattern}")
        
        return v
    
    @validator("cors_origins")
    def validate_cors_origins_in_production(cls, v, values):
        environment = values.get("environment", "development")
        
        if environment == "production" and v == "*":
            logger.warning("CORS origins set to '*' in production - consider restricting")
        
        return v

def load_enhanced_settings(environment: str = None) -> EnhancedSettings:
    """Load settings with secure configuration management"""
    
    # Initialize secure configuration
    config_manager = initialize_secure_configuration(environment)
    
    # Load environment variables
    env_vars = dict(os.environ)
    
    # Load from secure configuration manager
    secure_config = {}
    
    # Critical secrets from secure storage
    security_keys = [
        "SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_ENCRYPTION_KEY",
        "SESSION_SECRET", "CSRF_SECRET"
    ]
    
    for key in security_keys:
        value = config_manager.get_secret(key)
        if value:
            secure_config[key.lower()] = value
    
    # Load other configuration
    config_mapping = {
        # Environment variables -> Settings fields
        "ENVIRONMENT": "environment",
        "DEBUG": ("debug", lambda x: x.lower() == "true"),
        "HOST": "host",
        "PORT": ("port", int),
        "DATABASE_URL": "database_url",
        "VITE_API_HOST": "vite_api_host",
        "ALLOWED_HOSTS": ("allowed_hosts", lambda x: x.split(",")),
        "CORS_ORIGINS": "cors_origins",
        "ACCESS_TOKEN_EXPIRE_MINUTES": ("access_token_expire_minutes", int),
        "REFRESH_TOKEN_EXPIRE_DAYS": ("refresh_token_expire_days", int),
        "ALLOW_REGISTRATION": ("allow_registration", lambda x: x.lower() == "true"),
        "MAX_FILE_SIZE": ("max_file_size", int),
        "MAX_FILENAME_LENGTH": ("max_filename_length", int),
        "UPLOAD_TIMEOUT": ("upload_timeout", int),
        "ALLOWED_FILE_TYPES": ("allowed_file_types", lambda x: x.split(",")),
        "DEFAULT_MODEL": "default_model",
        "AVAILABLE_MODELS": ("available_models", lambda x: x.split(",")),
        "UPLOAD_DIR": ("upload_dir", Path),
        "TRANSCRIPTS_DIR": ("transcripts_dir", Path),
        "MODELS_DIR": ("models_dir", Path),
        "CACHE_DIR": ("cache_dir", Path),
        "REDIS_URL": "redis_url",
        "CELERY_BROKER_URL": "celery_broker_url",
        "LOG_LEVEL": "log_level",
        "LOG_FORMAT": "log_format",
        "HSTS_MAX_AGE": ("hsts_max_age", int),
        "CSP_ENABLED": ("csp_enabled", lambda x: x.lower() == "true"),
        "SECURITY_HEADERS_ENABLED": ("security_headers_enabled", lambda x: x.lower() == "true"),
        "RATE_LIMIT_ENABLED": ("rate_limit_enabled", lambda x: x.lower() == "true"),
        "SESSION_TIMEOUT": ("session_timeout", int)
    }
    
    settings_data = secure_config.copy()
    
    for env_key, setting_config in config_mapping.items():
        if env_key in env_vars:
            try:
                if isinstance(setting_config, tuple):
                    setting_key, converter = setting_config
                    settings_data[setting_key] = converter(env_vars[env_key])
                else:
                    settings_data[setting_config] = env_vars[env_key]
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid value for {env_key}: {env_vars[env_key]} ({e})")
    
    return EnhancedSettings(**settings_data)

# Load settings with secure configuration
def get_settings(environment: str = None) -> EnhancedSettings:
    """Get application settings"""
    return load_enhanced_settings(environment)
