"""
Application settings for the Whisper Transcriber API.
Enhanced with security validation and production readiness checks.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class SecurityValidationError(Exception):
    """Raised when security validation fails."""
    pass


# Known insecure values that should never be used
INSECURE_VALUES = {
    "password", "secret", "key", "changeme", "admin", "test", 
    "development", "production", "123456", "password123",
    "securepassword123", "mysecretkey", "your-secret-key-here",
    "fa218a99d59b539d6a89fc70cee35a8ac9ca4591c34e4e0dde0ca8b4ee3204da",  # Old insecure key
    ""  # Empty values
}


class Settings(BaseModel):
    """Application settings with security validation."""
    
    # Basic app settings
    app_name: str = "Whisper Transcriber"
    version: str = "1.0.0"
    debug: bool = Field(default=False)
    environment: str = Field(default="development")
    
    # Server settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8001)
    
    # Database settings
    database_url: str = Field(default="sqlite:///./whisper_dev.db")
    db_url: str = Field(default="sqlite:///./whisper_dev.db")  # Alias for compatibility
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    
    # Backend settings
    job_queue_backend: str = Field(default="thread")
    storage_backend: str = Field(default="local")
    
    # Development server settings
    vite_api_host: str = Field(default="localhost:8001")
    
    # Security settings - CRITICAL FOR PRODUCTION
    secret_key: str = Field(default="")
    jwt_secret_key: str = Field(default="")
    redis_password: str = Field(default="")
    database_encryption_key: str = Field(default="")
    admin_api_key: str = Field(default="")
    celery_secret_key: str = Field(default="")
    
    allowed_hosts: List[str] = Field(default=["*"])
    cors_origins: str = Field(default="*")  # Changed to string for split() compatibility
    
    # File upload settings
    max_file_size: int = Field(default=100 * 1024 * 1024)  # 100MB
    allowed_file_types: List[str] = Field(
        default=[
            "audio/wav", "audio/x-wav", "audio/wave",
            "audio/mp3", "audio/mpeg", "audio/x-mp3",
            "audio/m4a", "audio/mp4", "audio/x-m4a",
            "audio/flac", "audio/x-flac",
            "audio/ogg", "audio/webm",
            "audio/aac", "audio/x-aac"
        ]
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
    
    # Security validation settings
    enforce_security_validation: bool = Field(default=True)
    
    # Database migration settings
    auto_migrate: bool = Field(default=False)  # Enable automatic Alembic migrations on startup
    
    @validator('secret_key')
    def validate_secret_key(cls, v, values):
        """Validate SECRET_KEY meets security requirements."""
        environment = values.get('environment', 'development')
        enforce_validation = values.get('enforce_security_validation', True)
        
        if not enforce_validation:
            return v
            
        # Convert to string safely
        value_str = str(v) if v is not None else ""
        
        if environment == 'production':
            if not value_str:
                raise SecurityValidationError("SECRET_KEY is required in production")
            if len(value_str) < 32:
                raise SecurityValidationError("SECRET_KEY must be at least 32 characters in production")
            if value_str.lower() in INSECURE_VALUES:
                raise SecurityValidationError("SECRET_KEY cannot use insecure default values")
        elif environment == 'development':
            if not value_str:
                print("WARNING: SECRET_KEY is empty in development environment")
            elif value_str.lower() in INSECURE_VALUES:
                print("WARNING: SECRET_KEY uses insecure default value")
        
        return v
    
    @validator('jwt_secret_key')
    def validate_jwt_secret_key(cls, v, values):
        """Validate JWT_SECRET_KEY meets security requirements."""
        environment = values.get('environment', 'development')
        enforce_validation = values.get('enforce_security_validation', True)
        
        if not enforce_validation:
            return v
            
        # Convert to string safely
        value_str = str(v) if v is not None else ""
        
        if environment == 'production':
            if not value_str:
                raise SecurityValidationError("JWT_SECRET_KEY is required in production")
            if len(value_str) < 32:
                raise SecurityValidationError("JWT_SECRET_KEY must be at least 32 characters in production")
            if value_str.lower() in INSECURE_VALUES:
                raise SecurityValidationError("JWT_SECRET_KEY cannot use insecure default values")
        
        return v
    
    @validator('redis_password')
    def validate_redis_password(cls, v, values):
        """Validate REDIS_PASSWORD meets security requirements."""
        environment = values.get('environment', 'development')
        enforce_validation = values.get('enforce_security_validation', True)
        
        if not enforce_validation:
            return v
            
        # Convert to string safely
        value_str = str(v) if v is not None else ""
        
        if environment == 'production':
            if not value_str:
                raise SecurityValidationError("REDIS_PASSWORD is required in production")
            if len(value_str) < 16:
                raise SecurityValidationError("REDIS_PASSWORD must be at least 16 characters in production")
            if value_str.lower() in INSECURE_VALUES:
                raise SecurityValidationError("REDIS_PASSWORD cannot use insecure default values")
        
        return v
    
    @validator('cors_origins')
    def validate_cors_origins(cls, v, values):
        """Validate CORS origins for production security."""
        # Convert to string safely
        cors_value = str(v) if v is not None else "*"
        environment = values.get('environment', 'development')
        
        if environment == 'production' and cors_value == "*":
            print("WARNING: CORS_ORIGINS set to '*' in production - consider restricting to specific domains")
        
        return cors_value
    
    def validate_production_security(self) -> List[str]:
        """Comprehensive production security validation."""
        if self.environment != 'production':
            return []
        
        issues = []
        
        # Check all required secrets - safely handle potential ModelPrivateAttr
        secrets_to_check = [
            ('SECRET_KEY', 'secret_key'),
            ('JWT_SECRET_KEY', 'jwt_secret_key'), 
            ('REDIS_PASSWORD', 'redis_password'),
        ]
        
        for name, attr_name in secrets_to_check:
            try:
                # Get the attribute value safely
                value = getattr(self, attr_name, "")
                value_str = str(value) if value is not None else ""
                
                if not value_str or value_str == "":
                    issues.append(f"{name} is required but empty in production")
                elif len(value_str) < 16:
                    issues.append(f"{name} is too short for production (minimum 16 characters)")
                elif value_str.lower() in INSECURE_VALUES:
                    issues.append(f"{name} uses an insecure default value")
            except Exception as e:
                issues.append(f"Error validating {name}: {e}")
        
        # Check security configuration
        if self.debug:
            issues.append("DEBUG mode must be disabled in production")
        
        # Safe CORS check
        try:
            cors_value = str(self.cors_origins) if self.cors_origins is not None else ""
            if cors_value == "*":
                issues.append("CORS_ORIGINS should not be '*' in production")
        except Exception:
            pass  # Skip if unable to check
        
        # Safe allowed_hosts check
        try:
            if isinstance(self.allowed_hosts, list) and "localhost" in self.allowed_hosts:
                issues.append("ALLOWED_HOSTS should not include localhost in production")
        except Exception:
            pass  # Skip if unable to check
        
        return issues

def load_settings() -> Settings:
    """Load settings from environment variables with security validation."""
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
    
    # Enhanced mapping of env vars to settings with security fields
    env_mapping = {
        "ENVIRONMENT": ("environment", str),
        "DEBUG": ("debug", lambda x: x.lower() == "true"),
        "HOST": ("host", str),
        "PORT": ("port", int),
        "DATABASE_URL": ("database_url", str),
        
        # Security settings - CRITICAL
        "SECRET_KEY": ("secret_key", str),
        "JWT_SECRET_KEY": ("jwt_secret_key", str),
        "REDIS_PASSWORD": ("redis_password", str),
        "DATABASE_ENCRYPTION_KEY": ("database_encryption_key", str),
        "ADMIN_API_KEY": ("admin_api_key", str),
        "CELERY_SECRET_KEY": ("celery_secret_key", str),
        
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
        "ENFORCE_SECURITY_VALIDATION": ("enforce_security_validation", lambda x: x.lower() == "true"),
    }
    
    for env_key, (setting_key, converter) in env_mapping.items():
        if env_key in env_vars:
            try:
                settings_data[setting_key] = converter(env_vars[env_key])
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid value for {env_key}: {env_vars[env_key]} ({e})")
    
    try:
        # Create settings instance with proper error handling
        settings_instance = Settings(**settings_data)
        
        # Debug: Print what we loaded for security fields
        print(f"DEBUG: Loaded SECRET_KEY: {'<set>' if settings_instance.secret_key else '<empty>'}")
        print(f"DEBUG: Loaded JWT_SECRET_KEY: {'<set>' if settings_instance.jwt_secret_key else '<empty>'}")
        print(f"DEBUG: Environment: {settings_instance.environment}")
        
        # Run production security validation if in production
        if settings_instance.environment == 'production':
            security_issues = settings_instance.validate_production_security()
            if security_issues:
                print("\n🚨 CRITICAL SECURITY ISSUES DETECTED:")
                for issue in security_issues:
                    print(f"   ❌ {issue}")
                print("\n💀 PRODUCTION DEPLOYMENT BLOCKED - Fix security issues above")
                if settings_instance.enforce_security_validation:
                    sys.exit(1)
        
        return settings_instance
        
    except SecurityValidationError as e:
        print(f"\n🚨 SECURITY VALIDATION FAILED: {e}")
        print("💀 Application cannot start with insecure configuration")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading settings: {e}")
        print("🔄 Creating settings with defaults and retrying...")
        
        # Try to create settings with minimal data to avoid Pydantic issues
        try:
            minimal_settings = Settings(
                secret_key=env_vars.get("SECRET_KEY", ""),
                jwt_secret_key=env_vars.get("JWT_SECRET_KEY", ""),
                environment=env_vars.get("ENVIRONMENT", "development"),
                database_url=env_vars.get("DATABASE_URL", "sqlite:///./whisper_dev.db"),
                redis_url=env_vars.get("REDIS_URL"),
                debug=env_vars.get("DEBUG", "").lower() == "true"
            )
            print("✅ Successfully created settings with minimal configuration")
            return minimal_settings
        except Exception as fallback_error:
            print(f"❌ Fallback settings creation failed: {fallback_error}")
            # Return completely default settings as last resort
            return Settings()


# Global settings instance
settings = load_settings()

# Production security check on module import
if settings.environment == 'production':
    security_issues = settings.validate_production_security()
    if security_issues and settings.enforce_security_validation:
        print("\n🛑 PRODUCTION SECURITY VALIDATION FAILED")
        print("The following critical security issues must be resolved:")
        for issue in security_issues:
            print(f"   💥 {issue}")
        print("\n🔒 Refer to .env.production.secure template for secure configuration")
        print("🔧 Run 'python scripts/validate_production_secrets.py' for detailed analysis")
        sys.exit(1)
