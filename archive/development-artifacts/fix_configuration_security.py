#!/usr/bin/env python3
"""
T026 Security Hardening - Configuration Security Fixes
Addresses weak secrets, hardcoded passwords, and insecure configuration management.
"""

import os
import secrets
import string
from pathlib import Path
from typing import Dict, List, Optional
import json

def generate_strong_secret(length: int = 32) -> str:
    """Generate a cryptographically strong secret key"""
    return secrets.token_urlsafe(length)

def generate_strong_password(length: int = 16) -> str:
    """Generate a strong password with mixed character types"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Ensure at least one of each character type
    if not any(c.islower() for c in password):
        password = password[:-1] + secrets.choice(string.ascii_lowercase)
    if not any(c.isupper() for c in password):
        password = password[:-1] + secrets.choice(string.ascii_uppercase)
    if not any(c.isdigit() for c in password):
        password = password[:-1] + secrets.choice(string.digits)
    if not any(c in "!@#$%^&*" for c in password):
        password = password[:-1] + secrets.choice("!@#$%^&*")
    
    return password

def create_secure_configuration_manager():
    """Create a secure configuration management system"""
    
    # Secure Configuration Manager
    config_manager_content = '''"""
Secure Configuration Manager for Whisper Transcriber
Handles environment-specific secrets and secure configuration loading.
"""

import os
import secrets
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
from api.utils.logger import get_system_logger
import base64
import hashlib

logger = get_system_logger("config_security")


class SecureConfigManager:
    """Secure configuration manager with encryption and environment-specific handling"""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.secrets_dir = Path("secrets")
        self.config_dir = Path("config")
        
        # Ensure directories exist
        self.secrets_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize encryption key
        self._init_encryption()
        
        # Load environment-specific configuration
        self._load_configuration()
    
    def _init_encryption(self):
        """Initialize encryption for sensitive data"""
        key_file = self.secrets_dir / "encryption.key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                self.encryption_key = f.read()
        else:
            # Generate new encryption key
            self.encryption_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self.encryption_key)
            # Secure the key file
            os.chmod(key_file, 0o600)
        
        self.cipher = Fernet(self.encryption_key)
    
    def _load_configuration(self):
        """Load environment-specific configuration"""
        self.config = {}
        
        # Base configuration
        base_config_file = self.config_dir / "base.json"
        if base_config_file.exists():
            with open(base_config_file) as f:
                self.config.update(json.load(f))
        
        # Environment-specific configuration
        env_config_file = self.config_dir / f"{self.environment}.json"
        if env_config_file.exists():
            with open(env_config_file) as f:
                self.config.update(json.load(f))
        
        # Load encrypted secrets
        self._load_encrypted_secrets()
    
    def _load_encrypted_secrets(self):
        """Load encrypted secrets from secure storage"""
        secrets_file = self.secrets_dir / f"secrets_{self.environment}.enc"
        
        if secrets_file.exists():
            try:
                with open(secrets_file, 'rb') as f:
                    encrypted_data = f.read()
                
                decrypted_data = self.cipher.decrypt(encrypted_data)
                secrets_config = json.loads(decrypted_data.decode())
                
                self.config.update(secrets_config)
                logger.info(f"Loaded encrypted secrets for {self.environment} environment")
                
            except Exception as e:
                logger.error(f"Failed to load encrypted secrets: {e}")
    
    def store_secret(self, key: str, value: str, encrypt: bool = True):
        """Store a secret securely"""
        if encrypt:
            secrets_file = self.secrets_dir / f"secrets_{self.environment}.enc"
            
            # Load existing secrets
            existing_secrets = {}
            if secrets_file.exists():
                try:
                    with open(secrets_file, 'rb') as f:
                        encrypted_data = f.read()
                    decrypted_data = self.cipher.decrypt(encrypted_data)
                    existing_secrets = json.loads(decrypted_data.decode())
                except Exception as e:
                    logger.warning(f"Could not load existing secrets: {e}")
            
            # Add new secret
            existing_secrets[key] = value
            
            # Encrypt and store
            data_to_encrypt = json.dumps(existing_secrets).encode()
            encrypted_data = self.cipher.encrypt(data_to_encrypt)
            
            with open(secrets_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Secure the file
            os.chmod(secrets_file, 0o600)
            
            logger.info(f"Stored encrypted secret: {key}")
        else:
            # Store in plain text (for non-sensitive config)
            config_file = self.config_dir / f"{self.environment}.json"
            
            existing_config = {}
            if config_file.exists():
                with open(config_file) as f:
                    existing_config = json.load(f)
            
            existing_config[key] = value
            
            with open(config_file, 'w') as f:
                json.dump(existing_config, f, indent=2)
            
            logger.info(f"Stored configuration: {key}")
        
        # Update in-memory config
        self.config[key] = value
    
    def get_secret(self, key: str, default: Any = None) -> Any:
        """Get a secret value"""
        return self.config.get(key, default)
    
    def generate_secret_key(self, length: int = 32) -> str:
        """Generate a cryptographically strong secret key"""
        return secrets.token_urlsafe(length)
    
    def generate_password(self, length: int = 16) -> str:
        """Generate a strong password"""
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Ensure character diversity
        if not any(c.islower() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_lowercase)
        if not any(c.isupper() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_uppercase)
        if not any(c.isdigit() for c in password):
            password = password[:-1] + secrets.choice(string.digits)
        if not any(c in "!@#$%^&*" for c in password):
            password = password[:-1] + secrets.choice("!@#$%^&*")
        
        return password
    
    def validate_secret_strength(self, secret: str) -> Dict[str, Any]:
        """Validate the strength of a secret"""
        issues = []
        score = 0
        
        # Length check
        if len(secret) < 12:
            issues.append("Secret is too short (minimum 12 characters)")
        elif len(secret) >= 32:
            score += 25
        elif len(secret) >= 16:
            score += 15
        else:
            score += 5
        
        # Character diversity
        has_lower = any(c.islower() for c in secret)
        has_upper = any(c.isupper() for c in secret)
        has_digit = any(c.isdigit() for c in secret)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in secret)
        
        diversity_score = sum([has_lower, has_upper, has_digit, has_special])
        score += diversity_score * 10
        
        if diversity_score < 3:
            issues.append("Secret should contain at least 3 character types")
        
        # Check for common weak patterns
        weak_patterns = [
            "password", "admin", "test", "dev", "secret",
            "change", "production", "123", "abc"
        ]
        
        secret_lower = secret.lower()
        for pattern in weak_patterns:
            if pattern in secret_lower:
                issues.append(f"Secret contains weak pattern: {pattern}")
                score -= 20
        
        # Entropy estimation
        import math
        unique_chars = len(set(secret))
        if unique_chars < len(secret) * 0.7:
            issues.append("Secret has low character diversity")
            score -= 10
        
        return {
            "score": max(0, score),
            "strength": "Strong" if score >= 70 else "Medium" if score >= 40 else "Weak",
            "issues": issues
        }
    
    def rotate_secrets(self):
        """Rotate all secrets with new strong values"""
        logger.info("Starting secret rotation process")
        
        secrets_to_rotate = [
            ("SECRET_KEY", self.generate_secret_key(32)),
            ("JWT_SECRET_KEY", self.generate_secret_key(32)),
            ("DATABASE_ENCRYPTION_KEY", self.generate_secret_key(32)),
            ("SESSION_SECRET", self.generate_secret_key(24)),
            ("CSRF_SECRET", self.generate_secret_key(24))
        ]
        
        for key, value in secrets_to_rotate:
            self.store_secret(key, value, encrypt=True)
            logger.info(f"Rotated secret: {key}")
        
        logger.info("Secret rotation completed")
    
    def audit_configuration(self) -> Dict[str, Any]:
        """Audit current configuration for security issues"""
        issues = []
        warnings = []
        recommendations = []
        
        # Check for weak secrets
        critical_secrets = ["SECRET_KEY", "JWT_SECRET_KEY"]
        for secret_key in critical_secrets:
            value = self.get_secret(secret_key)
            if value:
                validation = self.validate_secret_strength(value)
                if validation["strength"] == "Weak":
                    issues.append(f"{secret_key} is weak: {', '.join(validation['issues'])}")
                elif validation["strength"] == "Medium":
                    warnings.append(f"{secret_key} could be stronger")
        
        # Check for default values
        default_secrets = [
            "dev-secret-key-change-in-production",
            "change_this_in_production_use_secrets_token_hex_32",
            "your-secret-key-change-in-production"
        ]
        
        for secret_key, value in self.config.items():
            if isinstance(value, str) and value in default_secrets:
                issues.append(f"{secret_key} is using a default value")
        
        # Check environment settings
        if self.environment == "production":
            prod_requirements = {
                "DEBUG": False,
                "LOG_LEVEL": ["INFO", "WARNING", "ERROR"],
                "ENVIRONMENT": "production"
            }
            
            for key, expected in prod_requirements.items():
                actual = self.get_secret(key)
                if isinstance(expected, list):
                    if actual not in expected:
                        warnings.append(f"Production setting {key} should be one of {expected}")
                else:
                    if actual != expected:
                        warnings.append(f"Production setting {key} should be {expected}")
        
        # Security recommendations
        if not self.get_secret("HSTS_MAX_AGE"):
            recommendations.append("Enable HSTS for production")
        
        if not self.get_secret("CSP_ENABLED"):
            recommendations.append("Enable Content Security Policy")
        
        return {
            "issues": issues,
            "warnings": warnings,
            "recommendations": recommendations,
            "total_secrets": len([k for k in self.config.keys() if "secret" in k.lower() or "key" in k.lower()]),
            "environment": self.environment
        }
    
    def export_env_template(self, include_secrets: bool = False) -> str:
        """Export configuration as environment template"""
        lines = [f"# Configuration for {self.environment} environment"]
        lines.append(f"# Generated on {os.popen('date').read().strip()}")
        lines.append("")
        
        for key, value in sorted(self.config.items()):
            if "secret" in key.lower() or "password" in key.lower() or "key" in key.lower():
                if include_secrets:
                    lines.append(f"{key}={value}")
                else:
                    lines.append(f"{key}=CHANGE_THIS_SECRET")
            else:
                lines.append(f"{key}={value}")
        
        return "\\n".join(lines)


# Global configuration manager instance
_config_manager = None

def get_config_manager(environment: str = None) -> SecureConfigManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = SecureConfigManager(environment)
    return _config_manager

def initialize_secure_configuration(environment: str = None) -> SecureConfigManager:
    """Initialize secure configuration management"""
    config_manager = get_config_manager(environment)
    
    # Generate initial secrets if they don't exist
    required_secrets = {
        "SECRET_KEY": 32,
        "JWT_SECRET_KEY": 32,
        "DATABASE_ENCRYPTION_KEY": 32,
        "SESSION_SECRET": 24,
        "CSRF_SECRET": 24
    }
    
    for secret_name, length in required_secrets.items():
        if not config_manager.get_secret(secret_name):
            secret_value = config_manager.generate_secret_key(length)
            config_manager.store_secret(secret_name, secret_value, encrypt=True)
            logger.info(f"Generated new secret: {secret_name}")
    
    return config_manager
'''

    # Enhanced Settings with Secure Configuration
    enhanced_settings_content = '''"""
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
    port: int = Field(default=8000)
    
    # Database settings
    database_url: str = Field(default="sqlite:///./whisper_dev.db")
    db_url: str = Field(default="sqlite:///./whisper_dev.db")  # Alias for compatibility
    
    # Backend settings
    job_queue_backend: str = Field(default="thread")
    storage_backend: str = Field(default="local")
    
    # Development server settings
    vite_api_host: str = Field(default="localhost:8000")
    
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
'''

    # Create the files
    config_dir = Path("api/config")
    config_dir.mkdir(exist_ok=True)
    
    # Write secure configuration manager
    with open(config_dir / "secure_config_manager.py", 'w') as f:
        f.write(config_manager_content)
    print(f"Created secure configuration manager: {config_dir / 'secure_config_manager.py'}")
    
    # Write enhanced settings
    with open(config_dir / "enhanced_settings.py", 'w') as f:
        f.write(enhanced_settings_content)
    print(f"Created enhanced settings: {config_dir / 'enhanced_settings.py'}")
    
    # Create __init__.py for the config package
    with open(config_dir / "__init__.py", 'w') as f:
        f.write('"""Secure configuration management package"""\\n')
    
    return config_dir

def fix_hardcoded_secrets():
    """Fix hardcoded secrets in the codebase"""
    
    print("\\n=== Fixing Hardcoded Secrets ===")
    
    # Fix settings.py
    settings_path = Path("api/settings.py")
    if settings_path.exists():
        with open(settings_path, 'r') as f:
            content = f.read()
        
        # Replace weak default secret
        new_content = content.replace(
            'secret_key: str = Field(default="dev-secret-key-change-in-production")',
            'secret_key: str = Field(default="")'
        )
        
        with open(settings_path, 'w') as f:
            f.write(new_content)
        print(f"✅ Fixed weak default secret in {settings_path}")
    
    # Fix app/main.py
    app_main_path = Path("app/main.py")
    if app_main_path.exists():
        with open(app_main_path, 'r') as f:
            content = f.read()
        
        # Replace weak default secret
        new_content = content.replace(
            'SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")',
            'SECRET_KEY = os.getenv("SECRET_KEY", "")'
        )
        
        with open(app_main_path, 'w') as f:
            f.write(new_content)
        print(f"✅ Fixed weak default secret in {app_main_path}")
    
    # Fix admin password in users.py
    users_path = Path("api/services/users.py")
    if users_path.exists():
        with open(users_path, 'r') as f:
            content = f.read()
        
        # Generate a strong temporary password
        strong_password = generate_strong_password(20)
        
        # Replace weak admin password
        new_content = content.replace(
            'hashed_password=hash_password("admin123"),  # Change in production',
            f'hashed_password=hash_password("{strong_password}"),  # Strong generated password'
        )
        
        with open(users_path, 'w') as f:
            f.write(new_content)
        print(f"✅ Fixed weak admin password in {users_path}")
        print(f"   New admin password: {strong_password}")

def create_environment_specific_configs():
    """Create secure environment-specific configuration files"""
    
    print("\\n=== Creating Environment-Specific Configs ===")
    
    configs = {
        "development": {
            "DEBUG": True,
            "LOG_LEVEL": "DEBUG",
            "ENVIRONMENT": "development",
            "HSTS_MAX_AGE": 0,
            "CSP_ENABLED": False,
            "RATE_LIMIT_ENABLED": False,
            "ALLOW_REGISTRATION": True,
            "CORS_ORIGINS": "http://localhost:3000,http://localhost:5173",
            "ACCESS_TOKEN_EXPIRE_MINUTES": 60
        },
        "production": {
            "DEBUG": False,
            "LOG_LEVEL": "INFO",
            "ENVIRONMENT": "production",
            "HSTS_MAX_AGE": 31536000,
            "CSP_ENABLED": True,
            "RATE_LIMIT_ENABLED": True,
            "ALLOW_REGISTRATION": False,
            "CORS_ORIGINS": "https://yourdomain.com",
            "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
            "SECURITY_HEADERS_ENABLED": True
        },
        "test": {
            "DEBUG": False,
            "LOG_LEVEL": "WARNING",
            "ENVIRONMENT": "test",
            "HSTS_MAX_AGE": 0,
            "CSP_ENABLED": False,
            "RATE_LIMIT_ENABLED": False,
            "ALLOW_REGISTRATION": True,
            "CORS_ORIGINS": "*",
            "ACCESS_TOKEN_EXPIRE_MINUTES": 5
        }
    }
    
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    for env_name, config in configs.items():
        config_file = config_dir / f"{env_name}.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Created {env_name} configuration: {config_file}")

def generate_secure_secrets():
    """Generate and store secure secrets"""
    
    print("\\n=== Generating Secure Secrets ===")
    
    secrets_to_generate = {
        "SECRET_KEY": 32,
        "JWT_SECRET_KEY": 32,
        "DATABASE_ENCRYPTION_KEY": 32,
        "SESSION_SECRET": 24,
        "CSRF_SECRET": 24,
        "ADMIN_PASSWORD": 20  # Strong password
    }
    
    generated_secrets = {}
    
    for secret_name, length in secrets_to_generate.items():
        if secret_name == "ADMIN_PASSWORD":
            secret_value = generate_strong_password(length)
        else:
            secret_value = generate_strong_secret(length)
        
        generated_secrets[secret_name] = secret_value
        print(f"✅ Generated {secret_name}: {secret_value[:8]}...")
    
    return generated_secrets

def create_secure_env_files():
    """Create secure .env files for different environments"""
    
    print("\\n=== Creating Secure Environment Files ===")
    
    # Generate secrets
    secrets = generate_secure_secrets()
    
    # Development .env
    dev_env_content = f'''# Development Environment Configuration
# This file contains secrets - DO NOT commit to version control

# ===============================================
# 🔐 SECURITY CONFIGURATION
# ===============================================

SECRET_KEY={secrets["SECRET_KEY"]}
JWT_SECRET_KEY={secrets["JWT_SECRET_KEY"]}
DATABASE_ENCRYPTION_KEY={secrets["DATABASE_ENCRYPTION_KEY"]}
SESSION_SECRET={secrets["SESSION_SECRET"]}
CSRF_SECRET={secrets["CSRF_SECRET"]}

# ===============================================
# 🌐 APPLICATION CONFIGURATION
# ===============================================

ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
HOST=0.0.0.0
PORT=8000

# ===============================================
# 🗄️ DATABASE CONFIGURATION
# ===============================================

DATABASE_URL=sqlite:///./whisper_dev.db

# ===============================================
# 🚀 SERVER CONFIGURATION
# ===============================================

VITE_API_HOST=http://localhost:8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# ===============================================
# 👤 AUTHENTICATION CONFIGURATION
# ===============================================

ALLOW_REGISTRATION=true
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# ===============================================
# 📁 FILE UPLOAD CONFIGURATION
# ===============================================

MAX_FILE_SIZE=104857600  # 100MB
MAX_FILENAME_LENGTH=255
UPLOAD_TIMEOUT=300
ALLOWED_FILE_TYPES=audio/wav,audio/mp3,audio/m4a,audio/flac

# ===============================================
# 🔒 SECURITY CONFIGURATION
# ===============================================

HSTS_MAX_AGE=0  # Disabled for development
CSP_ENABLED=false
SECURITY_HEADERS_ENABLED=true
RATE_LIMIT_ENABLED=false

# ===============================================
# 📊 LOGGING CONFIGURATION
# ===============================================

LOG_FORMAT=standard
'''
    
    # Production .env template
    prod_env_content = f'''# Production Environment Configuration
# Copy this file to .env.prod and customize for your production environment
# IMPORTANT: Generate new secrets for production!

# ===============================================
# 🔐 SECURITY CONFIGURATION (CHANGE ALL SECRETS!)
# ===============================================

SECRET_KEY=GENERATE_NEW_SECRET_FOR_PRODUCTION
JWT_SECRET_KEY=GENERATE_NEW_SECRET_FOR_PRODUCTION
DATABASE_ENCRYPTION_KEY=GENERATE_NEW_SECRET_FOR_PRODUCTION
SESSION_SECRET=GENERATE_NEW_SECRET_FOR_PRODUCTION
CSRF_SECRET=GENERATE_NEW_SECRET_FOR_PRODUCTION

# ===============================================
# 🌐 APPLICATION CONFIGURATION
# ===============================================

ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# ===============================================
# 🗄️ DATABASE CONFIGURATION
# ===============================================

DATABASE_URL=postgresql://user:password@localhost/whisper_prod

# ===============================================
# 🚀 SERVER CONFIGURATION
# ===============================================

VITE_API_HOST=https://yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# ===============================================
# 👤 AUTHENTICATION CONFIGURATION
# ===============================================

ALLOW_REGISTRATION=false
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ===============================================
# 📁 FILE UPLOAD CONFIGURATION
# ===============================================

MAX_FILE_SIZE=524288000  # 500MB
MAX_FILENAME_LENGTH=255
UPLOAD_TIMEOUT=600
ALLOWED_FILE_TYPES=audio/wav,audio/mp3,audio/m4a,audio/flac

# ===============================================
# 🔒 SECURITY CONFIGURATION
# ===============================================

HSTS_MAX_AGE=31536000  # 1 year
CSP_ENABLED=true
SECURITY_HEADERS_ENABLED=true
RATE_LIMIT_ENABLED=true

# ===============================================
# 📊 LOGGING CONFIGURATION
# ===============================================

LOG_FORMAT=json
'''
    
    # Write development .env
    with open(".env.dev", 'w') as f:
        f.write(dev_env_content)
    print("✅ Created secure development environment file: .env.dev")
    
    # Write production template
    with open(".env.prod.template", 'w') as f:
        f.write(prod_env_content)
    print("✅ Created production environment template: .env.prod.template")
    
    # Store admin password securely
    secrets_dir = Path("secrets")
    secrets_dir.mkdir(exist_ok=True)
    
    with open(secrets_dir / "admin_password.txt", 'w') as f:
        f.write(secrets["ADMIN_PASSWORD"])
    os.chmod(secrets_dir / "admin_password.txt", 0o600)
    print(f"✅ Stored admin password securely: secrets/admin_password.txt")
    
    return secrets

def main():
    """Main function to fix configuration security issues"""
    
    print("🔒 T026 Security Hardening - Configuration Security Fixes")
    print("=" * 60)
    
    # Create secure configuration management system
    config_dir = create_secure_configuration_manager()
    print(f"✅ Created secure configuration system in {config_dir}")
    
    # Fix hardcoded secrets
    fix_hardcoded_secrets()
    
    # Create environment-specific configurations
    create_environment_specific_configs()
    
    # Generate and store secure secrets
    secrets = create_secure_env_files()
    
    print("\\n" + "=" * 60)
    print("✅ Configuration security fixes completed!")
    print("\\n📋 Summary of changes:")
    print("   • Created secure configuration management system")
    print("   • Fixed hardcoded weak secrets")
    print("   • Generated strong cryptographic secrets")
    print("   • Created environment-specific configurations")
    print("   • Enhanced settings with security validation")
    print("\\n⚠️  IMPORTANT:")
    print("   • Review generated admin password in secrets/admin_password.txt")
    print("   • Use .env.dev for development")
    print("   • Generate new secrets for production using .env.prod.template")
    print("   • Never commit .env files to version control")

if __name__ == "__main__":
    main()