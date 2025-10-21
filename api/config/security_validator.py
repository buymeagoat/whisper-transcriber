"""
Enhanced Configuration Validator with Security Checks
Replaces the basic config_validator.py with comprehensive security validation.
"""

import os
import re
import secrets
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from api.utils.logger import get_system_logger

logger = get_system_logger("config_security")


class ConfigurationSecurityValidator:
    """Comprehensive configuration security validator"""
    
    def __init__(self, environment: Optional[str] = None):
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.validation_results = {
            "errors": [],
            "warnings": [],
            "recommendations": [],
            "security_score": 0,
            "max_score": 100
        }
    
    def validate_secret_strength(self, secret: str, secret_name: str) -> Dict[str, Any]:
        """Validate the strength of a secret key"""
        issues = []
        score = 0
        
        if not secret:
            issues.append(f"{secret_name} is empty")
            return {"score": 0, "issues": issues, "strength": "Weak"}
        
        # Length requirements
        if len(secret) < 12:
            issues.append(f"{secret_name} is too short (minimum 12 characters)")
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
        
        diversity_count = sum([has_lower, has_upper, has_digit, has_special])
        score += diversity_count * 10
        
        if diversity_count < 3:
            issues.append(f"{secret_name} should contain at least 3 character types")
        
        # Check for weak patterns
        weak_patterns = [
            "password", "admin", "test", "dev", "secret",
            "change", "production", "123", "abc", "default",
            "demo", "sample", "example"
        ]
        
        secret_lower = secret.lower()
        for pattern in weak_patterns:
            if pattern in secret_lower:
                issues.append(f"{secret_name} contains weak pattern: {pattern}")
                score -= 20
        
        # Check for repeated characters
        if len(set(secret)) < len(secret) * 0.7:
            issues.append(f"{secret_name} has low character diversity")
            score -= 10
        
        # Check for keyboard patterns
        keyboard_patterns = [
            "qwerty", "asdf", "zxcv", "1234", "abcd",
            "qwertyuiop", "asdfghjkl", "zxcvbnm"
        ]
        
        for pattern in keyboard_patterns:
            if pattern in secret_lower:
                issues.append(f"{secret_name} contains keyboard pattern: {pattern}")
                score -= 15
        
        return {
            "score": max(0, score),
            "issues": issues,
            "strength": "Strong" if score >= 70 else "Medium" if score >= 40 else "Weak"
        }
    
    def validate_environment_config(self) -> None:
        """Validate environment-specific configuration"""
        
        if self.environment == "production":
            # Production-specific validations
            debug_mode = os.getenv("DEBUG", "false").lower()
            if debug_mode == "true":
                self.validation_results["errors"].append(
                    "DEBUG mode is enabled in production environment"
                )
            else:
                self.validation_results["security_score"] += 10
            
            # Check CORS settings
            cors_origins = os.getenv("CORS_ORIGINS", "*")
            if cors_origins == "*":
                self.validation_results["warnings"].append(
                    "CORS origins set to '*' in production - consider restricting"
                )
            else:
                self.validation_results["security_score"] += 5
            
            # Check HSTS settings
            hsts_max_age = os.getenv("HSTS_MAX_AGE", "0")
            if int(hsts_max_age) < 31536000:  # 1 year
                self.validation_results["warnings"].append(
                    "HSTS max-age should be at least 1 year (31536000) in production"
                )
            else:
                self.validation_results["security_score"] += 5
            
            # Check registration settings
            allow_registration = os.getenv("ALLOW_REGISTRATION", "true").lower()
            if allow_registration == "true":
                self.validation_results["warnings"].append(
                    "User registration is enabled in production - consider disabling"
                )
            else:
                self.validation_results["security_score"] += 5
        
        elif self.environment == "development":
            # Development-specific validations
            self.validation_results["recommendations"].append(
                "Using development environment - ensure production configs are ready"
            )
    
    def validate_secrets(self) -> None:
        """Validate all secret keys"""
        
        critical_secrets = [
            "SECRET_KEY",
            "JWT_SECRET_KEY", 
            "DATABASE_ENCRYPTION_KEY"
        ]
        
        important_secrets = [
            "SESSION_SECRET",
            "CSRF_SECRET"
        ]
        
        # Check critical secrets
        for secret_name in critical_secrets:
            secret_value = os.getenv(secret_name, "")
            validation = self.validate_secret_strength(secret_value, secret_name)
            
            if not validation["issues"]:  # No issues = strong
                self.validation_results["security_score"] += 10
            elif validation["strength"] == "Weak":
                self.validation_results["errors"].extend(
                    [f"CRITICAL: {issue}" for issue in validation["issues"]]
                )
            elif validation["strength"] == "Medium":
                self.validation_results["warnings"].extend(
                    [f"IMPORTANT: {issue}" for issue in validation["issues"]]
                )
                self.validation_results["security_score"] += 5
        
        # Check important secrets
        for secret_name in important_secrets:
            secret_value = os.getenv(secret_name, "")
            if secret_value:
                validation = self.validate_secret_strength(secret_value, secret_name)
                if validation["strength"] != "Weak":
                    self.validation_results["security_score"] += 3
            else:
                self.validation_results["recommendations"].append(
                    f"Consider setting {secret_name} for enhanced security"
                )
    
    def validate_file_security(self) -> None:
        """Validate file security settings"""
        
        # Check file size limits
        max_file_size = int(os.getenv("MAX_FILE_SIZE", "104857600"))  # 100MB default
        if max_file_size > 1073741824:  # 1GB
            self.validation_results["warnings"].append(
                f"Large file upload limit: {max_file_size // 1024 // 1024}MB - ensure adequate resources"
            )
        else:
            self.validation_results["security_score"] += 3
        
        # Check filename length
        max_filename_length = int(os.getenv("MAX_FILENAME_LENGTH", "255"))
        if max_filename_length > 255:
            self.validation_results["warnings"].append(
                "Filename length limit exceeds filesystem recommendations"
            )
        else:
            self.validation_results["security_score"] += 2
        
        # Check allowed file types
        allowed_types = os.getenv("ALLOWED_FILE_TYPES", "")
        if not allowed_types:
            self.validation_results["warnings"].append(
                "No file type restrictions configured - all file types allowed"
            )
        else:
            self.validation_results["security_score"] += 5
    
    def validate_authentication_config(self) -> None:
        """Validate authentication configuration"""
        
        # Token expiration
        access_token_expire = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        if access_token_expire > 480:  # 8 hours
            self.validation_results["warnings"].append(
                f"Access token expiration is very long: {access_token_expire} minutes"
            )
        elif access_token_expire <= 60:  # 1 hour or less
            self.validation_results["security_score"] += 5
        
        # Refresh token expiration
        refresh_token_expire = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        if refresh_token_expire > 30:
            self.validation_results["warnings"].append(
                f"Refresh token expiration is very long: {refresh_token_expire} days"
            )
        elif refresh_token_expire <= 7:
            self.validation_results["security_score"] += 3
    
    def validate_security_headers(self) -> None:
        """Validate security headers configuration"""
        
        security_headers_enabled = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower()
        if security_headers_enabled != "true":
            self.validation_results["warnings"].append(
                "Security headers are disabled"
            )
        else:
            self.validation_results["security_score"] += 5
        
        csp_enabled = os.getenv("CSP_ENABLED", "true").lower()
        if csp_enabled != "true" and self.environment == "production":
            self.validation_results["warnings"].append(
                "Content Security Policy is disabled in production"
            )
        elif csp_enabled == "true":
            self.validation_results["security_score"] += 5
    
    def validate_rate_limiting(self) -> None:
        """Validate rate limiting configuration"""
        
        rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower()
        if rate_limit_enabled != "true" and self.environment == "production":
            self.validation_results["warnings"].append(
                "Rate limiting is disabled in production"
            )
        elif rate_limit_enabled == "true":
            self.validation_results["security_score"] += 5
    
    def check_insecure_files(self) -> None:
        """Check for potentially insecure files"""
        
        insecure_patterns = [
            (".env", "Environment files should not be committed"),
            (".env.prod", "Production environment files should not be committed"),
            ("secrets/", "Secret files should not be committed"),
            ("*.key", "Key files should not be committed"),
            ("*.pem", "Certificate files should not be committed"),
            ("*.p12", "Certificate files should not be committed")
        ]
        
        project_root = Path(".")
        
        for pattern, warning in insecure_patterns:
            if "*" in pattern:
                # Glob pattern
                matches = list(project_root.glob(f"**/{pattern}"))
            else:
                # Direct path
                matches = [project_root / pattern] if (project_root / pattern).exists() else []
            
            for match in matches:
                if match.exists() and not any(exclude in str(match) for exclude in [".git", "venv", "__pycache__"]):
                    self.validation_results["warnings"].append(f"Found {match}: {warning}")
    
    def validate_database_security(self) -> None:
        """Validate database security settings"""
        
        database_url = os.getenv("DATABASE_URL", "")
        
        if database_url:
            # Check for hardcoded passwords in URL
            if re.search(r"://[^:]+:[^@]+@", database_url):
                self.validation_results["warnings"].append(
                    "Database URL contains embedded credentials - consider using environment variables"
                )
            
            # Check for SQLite in production
            if self.environment == "production" and database_url.startswith("sqlite"):
                self.validation_results["recommendations"].append(
                    "Consider using PostgreSQL or MySQL for production instead of SQLite"
                )
            elif not database_url.startswith("sqlite"):
                self.validation_results["security_score"] += 5
    
    def generate_security_recommendations(self) -> List[str]:
        """Generate security recommendations based on current config"""
        
        recommendations = []
        
        # Based on security score
        if self.validation_results["security_score"] < 50:
            recommendations.append("URGENT: Security score is low - review all security settings")
        elif self.validation_results["security_score"] < 70:
            recommendations.append("IMPORTANT: Security could be improved - address warnings")
        
        # Environment-specific recommendations
        if self.environment == "production":
            recommendations.extend([
                "Enable monitoring and alerting for security events",
                "Regularly rotate secrets and certificates",
                "Implement backup and disaster recovery procedures",
                "Consider implementing WAF (Web Application Firewall)",
                "Set up security scanning and vulnerability assessments"
            ])
        
        return recommendations
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete configuration security validation"""
        
        logger.info(f"Starting configuration security validation for {self.environment} environment")
        
        # Run all validation checks
        self.validate_environment_config()
        self.validate_secrets()
        self.validate_file_security()
        self.validate_authentication_config()
        self.validate_security_headers()
        self.validate_rate_limiting()
        self.check_insecure_files()
        self.validate_database_security()
        
        # Generate recommendations
        generated_recommendations = self.generate_security_recommendations()
        self.validation_results["recommendations"].extend(generated_recommendations)
        
        # Calculate final security grade
        score = self.validation_results["security_score"]
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        self.validation_results["security_grade"] = grade
        self.validation_results["environment"] = self.environment
        
        logger.info(f"Configuration validation completed. Grade: {grade}, Score: {score}/100")
        
        return self.validation_results


def validate_config(environment: Optional[str] = None) -> Dict[str, Any]:
    """Main configuration validation function"""
    
    validator = ConfigurationSecurityValidator(environment)
    return validator.run_full_validation()


def print_validation_results(results: Dict[str, Any]) -> None:
    """Print validation results in a readable format"""
    
    print(f"\\n🔒 Configuration Security Report - {results['environment'].upper()} Environment")
    print("=" * 70)
    
    # Security score and grade
    score = results['security_score']
    grade = results['security_grade']
    print(f"\\n📊 Security Score: {score}/100 (Grade: {grade})")
    
    # Color-coded grade
    if grade in ['A', 'B']:
        print("   ✅ Good security configuration")
    elif grade == 'C':
        print("   ⚠️  Acceptable security - improvements recommended")
    else:
        print("   ❌ Poor security configuration - immediate action required")
    
    # Errors (critical issues)
    if results['errors']:
        print(f"\\n❌ CRITICAL ISSUES ({len(results['errors'])})")
        for error in results['errors']:
            print(f"   • {error}")
    
    # Warnings (important issues)
    if results['warnings']:
        print(f"\\n⚠️  WARNINGS ({len(results['warnings'])})")
        for warning in results['warnings']:
            print(f"   • {warning}")
    
    # Recommendations
    if results['recommendations']:
        print(f"\\n💡 RECOMMENDATIONS ({len(results['recommendations'])})")
        for recommendation in results['recommendations']:
            print(f"   • {recommendation}")
    
    print("\\n" + "=" * 70)


if __name__ == "__main__":
    # Run validation
    results = validate_config()
    print_validation_results(results)