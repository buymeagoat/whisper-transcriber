"""
Configuration validator for the Whisper Transcriber API.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from api.settings import settings
from api.exceptions import ConfigurationError

def validate_config() -> Dict[str, Any]:
    """
    Validate application configuration.
    
    Returns:
        Dict with validation results
        
    Raises:
        ConfigurationError: If critical configuration is invalid
    """
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "info": []
    }
    
    # Check secret key
    if settings.secret_key == "dev-secret-key-change-in-production":
        if os.getenv("DEBUG", "false").lower() == "true":
            validation_results["warnings"].append("Using default secret key in development mode")
        else:
            validation_results["errors"].append("Default secret key must be changed in production")
            validation_results["valid"] = False
    
    # Check database URL
    if not settings.database_url:
        validation_results["errors"].append("DATABASE_URL is required")
        validation_results["valid"] = False
    
    # Check required directories
    required_dirs = [
        settings.upload_dir,
        settings.transcripts_dir,
        settings.models_dir,
        settings.cache_dir
    ]
    
    for directory in required_dirs:
        if not directory.exists():
            try:
                directory.mkdir(parents=True, exist_ok=True)
                validation_results["info"].append(f"Created directory: {directory}")
            except Exception as e:
                validation_results["errors"].append(f"Cannot create directory {directory}: {e}")
                validation_results["valid"] = False
    
    # Check file size limits
    if settings.max_file_size <= 0:
        validation_results["errors"].append("MAX_FILE_SIZE must be positive")
        validation_results["valid"] = False
    elif settings.max_file_size > 1024 * 1024 * 1024:  # 1GB
        validation_results["warnings"].append("MAX_FILE_SIZE is very large (>1GB)")
    
    # Check Whisper model
    if settings.default_model not in settings.available_models:
        validation_results["errors"].append(
            f"Default model '{settings.default_model}' not in available models"
        )
        validation_results["valid"] = False
    
    # Check ports
    if not (1 <= settings.port <= 65535):
        validation_results["errors"].append("PORT must be between 1 and 65535")
        validation_results["valid"] = False
    
    # Log validation results
    if validation_results["errors"]:
        error_msg = f"Configuration validation failed: {'; '.join(validation_results['errors'])}"
        if validation_results["valid"] is False:
            raise ConfigurationError(error_msg)
    
    return validation_results

def get_config_summary() -> Dict[str, Any]:
    """Get a summary of current configuration."""
    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "debug": settings.debug,
        "host": settings.host,
        "port": settings.port,
        "database_url": settings.database_url,
        "max_file_size_mb": settings.max_file_size // (1024 * 1024),
        "default_model": settings.default_model,
        "upload_dir": str(settings.upload_dir),
        "log_level": settings.log_level
    }
