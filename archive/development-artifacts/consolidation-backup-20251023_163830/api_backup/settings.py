"""
Application settings for the Whisper Transcriber API.
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field

class Settings(BaseModel):
    """Application settings."""
    
    # Basic app settings
    app_name: str = "Whisper Transcriber"
    version: str = "1.0.0"
    debug: bool = Field(default=False)
    
    # Server settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    
    # Database settings
    database_url: str = Field(default="sqlite:///./whisper_dev.db")
    db_url: str = Field(default="sqlite:///./whisper_dev.db")  # Alias for compatibility
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    
    # Backend settings
    job_queue_backend: str = Field(default="thread")
    storage_backend: str = Field(default="local")
    
    # Development server settings
    vite_api_host: str = Field(default="localhost:8000")
    
    # Security settings
    secret_key: str = Field(default="")
    allowed_hosts: List[str] = Field(default=["*"])
    cors_origins: str = Field(default="*")  # Changed to string for split() compatibility
    
    # File upload settings
    max_file_size: int = Field(default=100 * 1024 * 1024)  # 100MB
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

def load_settings() -> Settings:
    """Load settings from environment variables."""
    # Load from .env file if it exists
    env_file = Path(".env")
    env_vars = {}
    
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    
    # Override with actual environment variables
    env_vars.update(os.environ)
    
    # Convert environment variables to settings
    settings_data = {}
    
    # Simple mapping of env vars to settings
    env_mapping = {
        "DEBUG": ("debug", lambda x: x.lower() == "true"),
        "HOST": ("host", str),
        "PORT": ("port", int),
        "DATABASE_URL": ("database_url", str),
        "SECRET_KEY": ("secret_key", str),
        "ALLOWED_HOSTS": ("allowed_hosts", lambda x: x.split(",")),
        "CORS_ORIGINS": ("cors_origins", str),  # Keep as string for split() later,
        "MAX_FILE_SIZE": ("max_file_size", int),
        "ALLOWED_FILE_TYPES": ("allowed_file_types", lambda x: x.split(",")),
        "WHISPER_MODEL": ("default_model", str),
        "WHISPER_MODELS": ("available_models", lambda x: x.split(",")),
        "UPLOAD_DIR": ("upload_dir", Path),
        "TRANSCRIPTS_DIR": ("transcripts_dir", Path),
        "MODELS_DIR": ("models_dir", Path),
        "CACHE_DIR": ("cache_dir", Path),
        "REDIS_URL": ("redis_url", str),
        "CELERY_BROKER_URL": ("celery_broker_url", str),
        "LOG_LEVEL": ("log_level", str),
    }
    
    for env_key, (setting_key, converter) in env_mapping.items():
        if env_key in env_vars:
            try:
                settings_data[setting_key] = converter(env_vars[env_key])
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid value for {env_key}: {env_vars[env_key]} ({e})")
    
    return Settings(**settings_data)

# Global settings instance
settings = load_settings()
