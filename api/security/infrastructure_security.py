"""
Infrastructure Security Manager
Manages secure environment configuration and validates production secrets.
"""

import os
import re
import secrets
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


class SecretType(Enum):
    """Types of secrets that need to be managed."""
    CRYPTOGRAPHIC_KEY = "cryptographic_key"  # SECRET_KEY, JWT_SECRET
    DATABASE_PASSWORD = "database_password"  # Database passwords
    API_KEY = "api_key"  # External service API keys
    REDIS_PASSWORD = "redis_password"  # Redis authentication
    ADMIN_CREDENTIAL = "admin_credential"  # Admin passwords
    SIGNING_SECRET = "signing_secret"  # Token signing secrets


@dataclass
class SecretRequirement:
    """Requirements for a specific secret."""
    name: str
    secret_type: SecretType
    min_length: int
    required_in_production: bool
    description: str
    pattern: Optional[str] = None  # Regex pattern for validation
    generate_if_missing: bool = True


class InfrastructureSecurityManager:
    """Manages infrastructure security configuration and validation."""
    
    # Comprehensive secret requirements
    SECRET_REQUIREMENTS = [
        SecretRequirement(
            name="SECRET_KEY",
            secret_type=SecretType.CRYPTOGRAPHIC_KEY,
            min_length=32,
            required_in_production=True,
            description="Main application signing key for sessions and security",
            pattern=r"^[a-zA-Z0-9_\-]{32,}$"  # Allow URL-safe base64 characters
        ),
        SecretRequirement(
            name="JWT_SECRET_KEY",
            secret_type=SecretType.SIGNING_SECRET,
            min_length=32,
            required_in_production=True,
            description="JWT token signing secret",
            pattern=r"^[a-zA-Z0-9_\-]{32,}$"  # Allow URL-safe base64 characters
        ),
        SecretRequirement(
            name="REDIS_PASSWORD",
            secret_type=SecretType.REDIS_PASSWORD,
            min_length=16,
            required_in_production=True,
            description="Redis authentication password",
            pattern=r"^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]{16,}$"
        ),
        SecretRequirement(
            name="DATABASE_ENCRYPTION_KEY",
            secret_type=SecretType.CRYPTOGRAPHIC_KEY,
            min_length=32,
            required_in_production=True,
            description="Database encryption at rest key",
            pattern=r"^[a-zA-Z0-9_\-]{32,}$"  # Allow URL-safe base64 characters
        ),
        SecretRequirement(
            name="ADMIN_API_KEY",
            secret_type=SecretType.API_KEY,
            min_length=24,
            required_in_production=True,
            description="Administrative API access key",
            pattern=r"^[a-zA-Z0-9_\-]{24,}$"  # Allow URL-safe base64 characters
        ),
        SecretRequirement(
            name="CELERY_SECRET_KEY",
            secret_type=SecretType.CRYPTOGRAPHIC_KEY,
            min_length=32,
            required_in_production=True,
            description="Celery task queue encryption key",
            pattern=r"^[a-zA-Z0-9_\-]{32,}$"  # Allow URL-safe base64 characters
        ),
        SecretRequirement(
            name="OPENAI_API_KEY",
            secret_type=SecretType.API_KEY,
            min_length=20,
            required_in_production=False,
            description="OpenAI API key for enhanced features",
            pattern=r"^sk-[a-zA-Z0-9]{40,}$",
            generate_if_missing=False
        ),
        SecretRequirement(
            name="AWS_SECRET_ACCESS_KEY",
            secret_type=SecretType.API_KEY,
            min_length=20,
            required_in_production=False,
            description="AWS secret access key for cloud storage",
            generate_if_missing=False
        ),
    ]
    
    # Common insecure values that should never be used
    INSECURE_VALUES = {
        "password", "secret", "key", "changeme", "admin", "test", 
        "development", "production", "123456", "password123",
        "securepassword123", "mysecretkey", "your-secret-key-here",
        "fa218a99d59b539d6a89fc70cee35a8ac9ca4591c34e4e0dde0ca8b4ee3204da"  # Current insecure key
    }
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.env_files = {
            ".env": "Current environment (development)",
            ".env.development": "Development configuration", 
            ".env.production": "Production configuration",
            ".env.testing": "Testing configuration"
        }
        
    def generate_secure_secret(self, secret_type: SecretType, length: int = 32) -> str:
        """Generate a cryptographically secure secret."""
        if secret_type == SecretType.CRYPTOGRAPHIC_KEY:
            # Use base64 for better character diversity than hex
            import base64
            random_bytes = secrets.token_bytes(length)
            # Use URL-safe base64 and trim to exact length
            secret = base64.urlsafe_b64encode(random_bytes).decode('ascii')
            return secret[:length]
        elif secret_type == SecretType.REDIS_PASSWORD:
            # Include special characters for Redis passwords
            alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
            return ''.join(secrets.choice(alphabet) for _ in range(length))
        elif secret_type == SecretType.API_KEY:
            # Alphanumeric for API keys (URL-safe)
            return secrets.token_urlsafe(length)[:length]
        else:
            # Default: URL-safe base64 for maximum compatibility and diversity
            return secrets.token_urlsafe(length)[:length]
    
    def validate_secret(self, requirement: SecretRequirement, value: str) -> List[str]:
        """Validate a secret against its requirements."""
        issues = []
        
        if not value:
            if requirement.required_in_production:
                issues.append(f"{requirement.name} is required but empty")
            return issues
        
        # Check length
        if len(value) < requirement.min_length:
            issues.append(
                f"{requirement.name} must be at least {requirement.min_length} characters "
                f"(current: {len(value)})"
            )
        
        # Check pattern if provided
        if requirement.pattern and not re.match(requirement.pattern, value):
            issues.append(f"{requirement.name} does not match required pattern")
        
        # Check for insecure values
        if value.lower() in self.INSECURE_VALUES:
            issues.append(f"{requirement.name} uses an insecure default value")
        
        # Check for common weak patterns
        if self._is_weak_secret(value):
            issues.append(f"{requirement.name} appears to be weak or predictable")
        
        return issues
    
    def _is_weak_secret(self, value: str) -> bool:
        """Check if a secret appears weak or predictable."""
        # Check for repeated characters
        if len(set(value)) < len(value) * 0.5:
            return True
        
        # Check for common patterns
        weak_patterns = [
            r"^(.)\1{5,}",  # Repeated characters
            r"^(abc|123|qwe)",  # Sequential patterns
            r"(password|secret|key|admin)",  # Common words
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, value.lower()):
                return True
        
        return False
    
    def scan_hardcoded_secrets(self) -> List[Dict[str, Any]]:
        """Scan the repository for hardcoded secrets."""
        hardcoded_secrets = []
        
        # Improved patterns that detect hardcoded secrets (not env var references)
        secret_patterns = [
            (r'SECRET_KEY\s*=\s*["\']([^"\'$]{16,})["\']', 'SECRET_KEY'),  # Exclude $ references
            (r'password\s*=\s*["\']([^"\'$]{8,})["\']', 'Password'),
            (r'api_key\s*=\s*["\']([^"\'$]{16,})["\']', 'API Key'),
            (r'token\s*=\s*["\']([^"\'$]{16,})["\']', 'Token'),
            (r'REDIS_PASSWORD\s*=\s*["\']([^"\'$]{8,})["\']', 'Redis Password'),
            # Only detect hardcoded credentials in broker URLs, not env var references
            (r'://[^:]+:([^@$]{8,})@', 'Broker Password'),
        ]
        
        # Files to scan
        scan_patterns = [
            "**/*.py", "**/*.js", "**/*.yml", "**/*.yaml", 
            "**/*.json"
        ]
        
        # Only scan actual files, skip .env* files as they should contain variables
        for pattern in scan_patterns:
            for file_path in self.workspace_root.glob(pattern):
                if file_path.is_file() and not self._should_skip_file(file_path):
                    hardcoded_secrets.extend(
                        self._scan_file_for_secrets(file_path, secret_patterns)
                    )
        
        return hardcoded_secrets
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during secret scanning."""
        skip_patterns = [
            "venv/", "node_modules/", ".git/", "__pycache__/",
            "temp/", "cache/", "logs/", "archive/",
            "frontend/dist/",  # Build artifacts
            ".env.insecure.backup",  # Backup files
            "infrastructure_security.py",  # This file contains example patterns
            "test_auth_",  # Test files with test credentials
            "load_testing/",  # Load testing files with test data
            "create_test_user.py"  # Script that creates test users
        ]
        
        file_str = str(file_path)
        return any(pattern in file_str for pattern in skip_patterns)
    
    def _scan_file_for_secrets(self, file_path: Path, patterns: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """Scan a single file for hardcoded secrets."""
        secrets_found = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                for line_num, line in enumerate(content.splitlines(), 1):
                    for pattern_regex, secret_type in patterns:
                        matches = re.finditer(pattern_regex, line, re.IGNORECASE)
                        for match in matches:
                            secret_value = match.group(1) if match.groups() else match.group(0)
                            
                            # Skip if it looks like a placeholder or environment variable reference
                            if self._is_placeholder(secret_value) or self._is_env_var_reference(secret_value):
                                continue
                            
                            secrets_found.append({
                                "file": str(file_path.relative_to(self.workspace_root)),
                                "line": line_num,
                                "type": secret_type,
                                "value": secret_value[:20] + "..." if len(secret_value) > 20 else secret_value,
                                "severity": "HIGH" if len(secret_value) > 16 else "MEDIUM"
                            })
        
        except Exception as e:
            # Log error but continue scanning
            print(f"Warning: Could not scan {file_path}: {e}")
        
        return secrets_found
    
    def _is_placeholder(self, value: str) -> bool:
        """Check if a value appears to be a placeholder."""
        placeholder_indicators = [
            "your-", "replace-", "change-", "example-", 
            "placeholder", "REPLACE", "CHANGE", "TODO"
        ]
        return any(indicator in value for indicator in placeholder_indicators)
    
    def _is_env_var_reference(self, value: str) -> bool:
        """Check if a value is an environment variable reference."""
        # Check for ${VAR} or $VAR patterns
        env_var_patterns = [
            r'^\$\{[A-Z_][A-Z0-9_]*\}$',  # ${VAR_NAME}
            r'^\$[A-Z_][A-Z0-9_]*$',      # $VAR_NAME
        ]
        
        for pattern in env_var_patterns:
            if re.match(pattern, value):
                return True
        
        return False
    
    def create_secure_env_template(self, environment: str = "production") -> str:
        """Create a secure environment template with all required secrets."""
        template_lines = [
            f"# {environment.title()} Environment Configuration",
            f"# Generated by Infrastructure Security Manager",
            f"# Copy to .env.{environment} and configure with real values",
            "",
            "# ============================================================================",
            "# CRITICAL SECURITY NOTICE",
            "# ============================================================================",
            "# All secrets below MUST be changed before production deployment.",
            "# Never commit real secrets to version control.",
            "# Use environment-specific secret management solutions.",
            "# ============================================================================",
            "",
            f"# Environment Configuration",
            f"ENVIRONMENT={environment}",
            f"DEBUG={'false' if environment == 'production' else 'true'}",
            "LOG_LEVEL=INFO",
            "",
        ]
        
        # Group secrets by type
        secret_groups = {}
        for requirement in self.SECRET_REQUIREMENTS:
            if requirement.secret_type not in secret_groups:
                secret_groups[requirement.secret_type] = []
            secret_groups[requirement.secret_type].append(requirement)
        
        # Add secrets by group
        for secret_type, requirements in secret_groups.items():
            template_lines.append(f"# {secret_type.value.replace('_', ' ').title()} Configuration")
            
            for requirement in requirements:
                template_lines.append(f"# {requirement.description}")
                
                if requirement.generate_if_missing and environment != "production":
                    # Generate example value for non-production
                    example_value = self.generate_secure_secret(
                        requirement.secret_type, 
                        requirement.min_length
                    )
                    template_lines.append(f"{requirement.name}={example_value}")
                else:
                    # Use placeholder for production
                    template_lines.append(f"{requirement.name}=your-{requirement.name.lower().replace('_', '-')}-here")
                
                template_lines.append("")
        
        # Add non-secret configuration
        template_lines.extend([
            "# Database Configuration",
            f"DATABASE_URL={'postgresql://user:password@localhost/whisper_prod' if environment == 'production' else 'sqlite:///./whisper_dev.db'}",
            "",
            "# Redis Configuration", 
            f"REDIS_URL=redis://:{'{REDIS_PASSWORD}'}@{'redis-host' if environment == 'production' else 'localhost'}:6379/0",
            "",
            "# Application Configuration",
            "MAX_FILE_SIZE=104857600",
            "MAX_CONCURRENT_JOBS=2",
            "CORS_ORIGINS=https://yourdomain.com" if environment == "production" else "http://localhost:3002,http://localhost:8001",
            "",
            "# Optional External Services",
            "# OPENAI_API_KEY=sk-your-openai-key-here",
            "# AWS_ACCESS_KEY_ID=your-aws-access-key-here", 
            "# AWS_SECRET_ACCESS_KEY=your-aws-secret-key-here",
            "# S3_BUCKET=your-s3-bucket-name",
            "",
            "# ============================================================================",
            "# SECURITY REMINDERS",
            "# ============================================================================",
            "# 1. Change ALL placeholder values above",
            "# 2. Use strong, unique secrets (32+ characters)",
            "# 3. Never commit this file with real secrets",
            "# 4. Use secret management tools in production",
            "# 5. Rotate secrets regularly",
            "# ============================================================================",
        ])
        
        return "\n".join(template_lines)
    
    def validate_environment(self, env_file: str = ".env") -> Dict[str, Any]:
        """Validate an environment configuration."""
        env_path = self.workspace_root / env_file
        
        result = {
            "file": env_file,
            "exists": env_path.exists(),
            "valid": True,
            "errors": [],
            "warnings": [],
            "secrets_status": {},
            "security_score": 0
        }
        
        if not env_path.exists():
            result["valid"] = False
            result["errors"].append(f"Environment file {env_file} does not exist")
            return result
        
        # Load environment variables
        env_vars = self._load_env_file(env_path)
        
        # Validate each secret requirement
        for requirement in self.SECRET_REQUIREMENTS:
            value = env_vars.get(requirement.name, "")
            issues = self.validate_secret(requirement, value)
            
            result["secrets_status"][requirement.name] = {
                "present": bool(value),
                "valid": len(issues) == 0,
                "issues": issues,
                "required": requirement.required_in_production
            }
            
            if issues:
                if requirement.required_in_production:
                    result["errors"].extend(issues)
                else:
                    result["warnings"].extend(issues)
        
        # Calculate security score
        total_requirements = len(self.SECRET_REQUIREMENTS)
        valid_secrets = sum(1 for status in result["secrets_status"].values() if status["valid"])
        result["security_score"] = int((valid_secrets / total_requirements) * 100)
        
        result["valid"] = len(result["errors"]) == 0
        
        return result
    
    def _load_env_file(self, env_path: Path) -> Dict[str, str]:
        """Load environment variables from a file."""
        env_vars = {}
        
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        except Exception as e:
            print(f"Warning: Could not load {env_path}: {e}")
        
        return env_vars
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate a comprehensive security report."""
        report = {
            "timestamp": self._get_timestamp(),
            "hardcoded_secrets": self.scan_hardcoded_secrets(),
            "environment_files": {},
            "recommendations": [],
            "overall_security_grade": "F"
        }
        
        # Validate all environment files
        for env_file, description in self.env_files.items():
            if (self.workspace_root / env_file).exists():
                report["environment_files"][env_file] = self.validate_environment(env_file)
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)
        
        # Calculate overall security grade
        report["overall_security_grade"] = self._calculate_security_grade(report)
        
        return report
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on the report."""
        recommendations = []
        
        # Check hardcoded secrets
        if report["hardcoded_secrets"]:
            recommendations.append(
                f"Found {len(report['hardcoded_secrets'])} hardcoded secrets. "
                "Move all secrets to environment variables."
            )
        
        # Check environment files
        for env_file, validation in report["environment_files"].items():
            if not validation["valid"]:
                recommendations.append(
                    f"Fix validation errors in {env_file}: {len(validation['errors'])} errors found"
                )
            
            if validation["security_score"] < 80:
                recommendations.append(
                    f"Improve security configuration in {env_file} "
                    f"(current score: {validation['security_score']}%)"
                )
        
        # General recommendations
        recommendations.extend([
            "Implement secret rotation procedures",
            "Use dedicated secret management tools in production",
            "Enable secret scanning in CI/CD pipeline",
            "Regular security audits of environment configuration"
        ])
        
        return recommendations
    
    def _calculate_security_grade(self, report: Dict[str, Any]) -> str:
        """Calculate overall security grade."""
        deductions = 0
        
        # Major deductions for hardcoded secrets
        deductions += len(report["hardcoded_secrets"]) * 20
        
        # Deductions based on environment file security scores
        if report["environment_files"]:
            avg_score = sum(
                validation["security_score"] 
                for validation in report["environment_files"].values()
            ) / len(report["environment_files"])
            
            deductions += (100 - avg_score) * 0.5
        
        final_score = max(0, 100 - deductions)
        
        if final_score >= 90:
            return "A"
        elif final_score >= 80:
            return "B" 
        elif final_score >= 70:
            return "C"
        elif final_score >= 60:
            return "D"
        else:
            return "F"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for reports."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"


# Global infrastructure security manager
infrastructure_security = InfrastructureSecurityManager()