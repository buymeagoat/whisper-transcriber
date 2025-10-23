"""
System logger utility for the Whisper Transcriber API.
"""

import logging
import sys
from typing import Optional
import os
from pathlib import Path

def get_system_logger(name: str = "whisper_api", level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured system logger.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if logs directory exists)
    logs_dir = Path("logs")
    if logs_dir.exists():
        file_handler = logging.FileHandler(logs_dir / "api.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_backend_logger(name: str = "whisper_backend") -> logging.Logger:
    """Get a logger for backend processes."""
    return get_system_logger(name)

def get_app_logger(name: str = "whisper_app") -> logging.Logger:
    """Get a logger for application-level events."""
    return get_system_logger(name)

def get_logger(name: str = "whisper_api") -> logging.Logger:
    """Alias for get_system_logger for backward compatibility."""
    return get_system_logger(name)
