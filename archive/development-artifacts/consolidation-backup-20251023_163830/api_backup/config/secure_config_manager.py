"""
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
        
        return "\n".join(lines)


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
