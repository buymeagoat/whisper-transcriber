"""
Test suite for configuration security enhancements
"""

import pytest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock

from api.config.security_validator import (
    ConfigurationSecurityValidator,
    validate_config,
    print_validation_results
)


class TestConfigurationSecurityValidator:
    """Test configuration security validator functionality"""
    
    def test_secret_strength_validation_empty(self):
        """Test validation of empty secrets"""
        validator = ConfigurationSecurityValidator("test")
        result = validator.validate_secret_strength("", "TEST_SECRET")
        
        assert result["strength"] == "Weak"
        assert result["score"] == 0
        assert "TEST_SECRET is empty" in result["issues"]
    
    def test_secret_strength_validation_weak(self):
        """Test validation of weak secrets"""
        validator = ConfigurationSecurityValidator("test")
        weak_secrets = [
            "123",
            "password",
            "admin123",
            "test-secret",
            "dev-key"
        ]
        
        for secret in weak_secrets:
            result = validator.validate_secret_strength(secret, "TEST_SECRET")
            assert result["strength"] == "Weak"
            assert result["score"] < 40
    
    def test_secret_strength_validation_strong(self):
        """Test validation of strong secrets"""
        validator = ConfigurationSecurityValidator("test")
        strong_secrets = [
            "uGZm-g8TqCeS1lG9kP5xNc-4vB2wYf7hRt8uE3qW9lK6jN0mL",  # 48 chars, mixed
            "RaTy5nTMbH3kF8pL2vC9xE6wQ1rT4uY7iO5nA0sD9fG8hJ!@#",  # 48 chars with special
            "A1b2C3d4E5f6G7h8I9j0K!@#$%^&*()_+-=[]{}|;:,.<>?"  # All character types
        ]
        
        for secret in strong_secrets:
            result = validator.validate_secret_strength(secret, "TEST_SECRET")
            assert result["strength"] == "Strong"
            assert result["score"] >= 70
    
    def test_environment_specific_validation_production(self):
        """Test production-specific validation"""
        with patch.dict(os.environ, {
            "DEBUG": "false",
            "CORS_ORIGINS": "https://mydomain.com",
            "HSTS_MAX_AGE": "31536000",
            "ALLOW_REGISTRATION": "false"
        }):
            validator = ConfigurationSecurityValidator("production")
            validator.validate_environment_config()
            
            # Should have no errors for proper production config
            assert len(validator.validation_results["errors"]) == 0
            assert validator.validation_results["security_score"] > 0
    
    def test_environment_specific_validation_production_errors(self):
        """Test production validation with configuration errors"""
        with patch.dict(os.environ, {
            "DEBUG": "true",  # Error: debug enabled in production
            "CORS_ORIGINS": "*",  # Warning: permissive CORS
            "HSTS_MAX_AGE": "0",  # Warning: HSTS disabled
            "ALLOW_REGISTRATION": "true"  # Warning: registration enabled
        }):
            validator = ConfigurationSecurityValidator("production")
            validator.validate_environment_config()
            
            # Should have errors for improper production config
            assert len(validator.validation_results["errors"]) > 0
            assert any("DEBUG mode is enabled" in error for error in validator.validation_results["errors"])
    
    def test_secrets_validation(self):
        """Test comprehensive secrets validation"""
        with patch.dict(os.environ, {
            "SECRET_KEY": "uGZm-g8TqCeS1lG9kP5xNc-4vB2wYf7hRt8uE3qW9lK6jN0mL",
            "JWT_SECRET_KEY": "RaTy5nTMbH3kF8pL2vC9xE6wQ1rT4uY7iO5nA0sD9fG8hJ",
            "DATABASE_ENCRYPTION_KEY": "AVVYHeHJ8mP3qW6tY9rE2uI5oP8sA1dF4gH7jK0lN3vB6xC"
        }):
            validator = ConfigurationSecurityValidator("production")
            validator.validate_secrets()
            
            # Should have high security score for strong secrets
            assert validator.validation_results["security_score"] >= 30
            assert len(validator.validation_results["errors"]) == 0
    
    def test_file_security_validation(self):
        """Test file security settings validation"""
        with patch.dict(os.environ, {
            "MAX_FILE_SIZE": "104857600",  # 100MB - reasonable
            "MAX_FILENAME_LENGTH": "255",  # Standard limit
            "ALLOWED_FILE_TYPES": "audio/wav,audio/mp3,audio/m4a"
        }):
            validator = ConfigurationSecurityValidator("production")
            validator.validate_file_security()
            
            # Should have positive security score for proper file config
            assert validator.validation_results["security_score"] > 0
    
    def test_authentication_config_validation(self):
        """Test authentication configuration validation"""
        with patch.dict(os.environ, {
            "ACCESS_TOKEN_EXPIRE_MINUTES": "30",  # Reasonable expiration
            "REFRESH_TOKEN_EXPIRE_DAYS": "7"  # Reasonable expiration
        }):
            validator = ConfigurationSecurityValidator("production")
            validator.validate_authentication_config()
            
            # Should have positive security score for proper auth config
            assert validator.validation_results["security_score"] > 0
    
    def test_security_headers_validation(self):
        """Test security headers configuration validation"""
        with patch.dict(os.environ, {
            "SECURITY_HEADERS_ENABLED": "true",
            "CSP_ENABLED": "true"
        }):
            validator = ConfigurationSecurityValidator("production")
            validator.validate_security_headers()
            
            # Should have positive security score for enabled security headers
            assert validator.validation_results["security_score"] > 0
    
    def test_rate_limiting_validation(self):
        """Test rate limiting configuration validation"""
        with patch.dict(os.environ, {
            "RATE_LIMIT_ENABLED": "true"
        }):
            validator = ConfigurationSecurityValidator("production")
            validator.validate_rate_limiting()
            
            # Should have positive security score for enabled rate limiting
            assert validator.validation_results["security_score"] > 0
    
    def test_database_security_validation(self):
        """Test database security validation"""
        # Test SQLite warning in production
        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///./production.db"
        }):
            validator = ConfigurationSecurityValidator("production")
            validator.validate_database_security()
            
            # Should recommend PostgreSQL for production
            assert any("PostgreSQL or MySQL" in rec for rec in validator.validation_results["recommendations"])
        
        # Test PostgreSQL in production (good)
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://user:pass@localhost/db"
        }):
            validator = ConfigurationSecurityValidator("production")
            validator.validate_database_security()
            
            # Should have positive security score
            assert validator.validation_results["security_score"] > 0
    
    def test_full_validation_integration(self):
        """Test complete validation process"""
        # Test with secure configuration
        secure_env = {
            "SECRET_KEY": "uGZm-g8TqCeS1lG9kP5xNc-4vB2wYf7hRt8uE3qW9lK6jN0mL",
            "JWT_SECRET_KEY": "RaTy5nTMbH3kF8pL2vC9xE6wQ1rT4uY7iO5nA0sD9fG8hJ",
            "DATABASE_ENCRYPTION_KEY": "AVVYHeHJ8mP3qW6tY9rE2uI5oP8sA1dF4gH7jK0lN3vB6xC",
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "CORS_ORIGINS": "https://mydomain.com",
            "HSTS_MAX_AGE": "31536000",
            "ALLOW_REGISTRATION": "false",
            "MAX_FILE_SIZE": "104857600",
            "ALLOWED_FILE_TYPES": "audio/wav,audio/mp3",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
            "SECURITY_HEADERS_ENABLED": "true",
            "CSP_ENABLED": "true",
            "RATE_LIMIT_ENABLED": "true",
            "DATABASE_URL": "postgresql://user:pass@localhost/db"
        }
        
        with patch.dict(os.environ, secure_env):
            results = validate_config("production")
            
            # Should have good security score
            assert results["security_score"] >= 70
            assert results["security_grade"] in ["A", "B", "C"]
            assert len(results["errors"]) == 0
    
    def test_print_validation_results(self, capsys):
        """Test validation results printing"""
        results = {
            "environment": "test",
            "security_score": 85,
            "security_grade": "B",
            "errors": ["Critical error"],
            "warnings": ["Warning message"],
            "recommendations": ["Recommendation"]
        }
        
        print_validation_results(results)
        captured = capsys.readouterr()
        
        assert "Security Score: 85/100" in captured.out
        assert "Grade: B" in captured.out
        assert "Critical error" in captured.out
        assert "Warning message" in captured.out
        assert "Recommendation" in captured.out


class TestSecureConfigurationIntegration:
    """Test integration with the secure configuration system"""
    
    def test_config_validator_import(self):
        """Test that config validator can be imported"""
        from api.config.security_validator import validate_config
        assert callable(validate_config)
    
    def test_environment_detection(self):
        """Test environment detection"""
        # Test default environment
        validator = ConfigurationSecurityValidator()
        assert validator.environment == "development"
        
        # Test explicit environment
        validator = ConfigurationSecurityValidator("production")
        assert validator.environment == "production"
        
        # Test environment from env var
        with patch.dict(os.environ, {"ENVIRONMENT": "test"}):
            validator = ConfigurationSecurityValidator()
            assert validator.environment == "test"


def test_basic_validation():
    """Basic validation test that can be run standalone"""
    print("\\nRunning basic configuration security validation test...")
    
    # Test with properly strong secrets (no weak patterns)
    test_env = {
        "SECRET_KEY": "K9mP3qW6tY8rE2uI5oP1sA4dF7gH0jL3vB6xC9zN2bM5kQ8wR",
        "JWT_SECRET_KEY": "R5tY8uI1oP4sA7dF0gH3jL6vB9xC2zN5bM8kQ1wE4rT7yU0iO",
        "DATABASE_ENCRYPTION_KEY": "F2gH5jL8vB1xC4zN7bM0kQ3wE6rT9yU2iO5pA8dG1fH4jK7l",
        "ENVIRONMENT": "test"
    }
    
    with patch.dict(os.environ, test_env):
        results = validate_config("test")
        
        print(f"Security Score: {results['security_score']}/100")
        print(f"Security Grade: {results['security_grade']}")
        print(f"Errors: {len(results['errors'])}")
        print(f"Warnings: {len(results['warnings'])}")
        
        # Should have good security with proper secrets
        assert results["security_score"] > 40
        assert len(results["errors"]) == 0  # No critical errors with proper secrets
        
        print("✅ Basic validation test passed!")


if __name__ == "__main__":
    # Run basic test
    test_basic_validation()
    
    print("\\n" + "="*50)
    print("Configuration Security Test Suite")
    print("="*50)
    print("\\nTo run full test suite:")
    print("pytest tests/test_configuration_security.py -v")
    print("\\nTo run configuration validation:")
    print("python -m api.config.security_validator")