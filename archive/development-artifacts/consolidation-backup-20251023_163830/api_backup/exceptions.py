"""
Custom exceptions for the Whisper Transcriber API.
"""

class WhisperAPIException(Exception):
    """Base exception for Whisper API errors."""
    pass

class ConfigurationError(WhisperAPIException):
    """Raised when there's a configuration error."""
    pass

class InitError(WhisperAPIException):
    """Raised when initialization fails."""
    pass

class ValidationError(WhisperAPIException):
    """Raised when validation fails."""
    pass

class ProcessingError(WhisperAPIException):
    """Raised when audio processing fails."""
    pass

class StorageError(WhisperAPIException):
    """Raised when storage operations fail."""
    pass

class AuthenticationError(WhisperAPIException):
    """Raised when authentication fails."""
    pass

class AuthorizationError(WhisperAPIException):
    """Raised when authorization fails."""
    pass

class RateLimitError(WhisperAPIException):
    """Raised when rate limits are exceeded."""
    pass
