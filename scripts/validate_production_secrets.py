#!/usr/bin/env python3
"""
Production Secret Validator
Validates production environment configuration for security compliance.
MUST pass before production deployment.
"""

import sys
import os
from pathlib import Path

# Add the API directory to the path so we can import our security module
sys.path.insert(0, str(Path(__file__).parent.parent))

from security.infrastructure_security import infrastructure_security, SecretType


def validate_production_secrets() -> bool:
    """Validate production secrets and environment configuration."""
    print("🔒 Production Secret Validation")
    print("=" * 50)
    
    success = True
    
    # Check for production environment file
    production_env = Path(".env.production")
    if not production_env.exists():
        print("❌ CRITICAL: .env.production file does not exist")
        print("   Create .env.production with secure configuration")
        success = False
        return success
    
    # Validate production environment
    print("📋 Validating production environment configuration...")
    validation = infrastructure_security.validate_environment(".env.production")
    
    if validation["valid"]:
        print(f"✅ Production environment validation passed")
        print(f"   Security Score: {validation['security_score']}%")
    else:
        print(f"❌ Production environment validation failed")
        print(f"   Security Score: {validation['security_score']}%")
        print(f"   Errors: {len(validation['errors'])}")
        
        for error in validation["errors"]:
            print(f"   - {error}")
        
        success = False
    
    # Scan for hardcoded secrets
    print("\n🔍 Scanning for hardcoded secrets...")
    hardcoded_secrets = infrastructure_security.scan_hardcoded_secrets()
    
    if hardcoded_secrets:
        print(f"❌ Found {len(hardcoded_secrets)} hardcoded secrets:")
        for secret in hardcoded_secrets[:10]:  # Show first 10
            print(f"   - {secret['file']}:{secret['line']} - {secret['type']} ({secret['severity']})")
        
        if len(hardcoded_secrets) > 10:
            print(f"   ... and {len(hardcoded_secrets) - 10} more")
        
        success = False
    else:
        print("✅ No hardcoded secrets found")
    
    # Generate security report
    print("\n📊 Generating security report...")
    report = infrastructure_security.generate_security_report()
    
    print(f"Overall Security Grade: {report['overall_security_grade']}")
    
    if report["overall_security_grade"] in ["D", "F"]:
        print("❌ Security grade too low for production deployment")
        success = False
    elif report["overall_security_grade"] == "C":
        print("⚠️  Security grade marginal - consider improvements")
    else:
        print("✅ Security grade acceptable for production")
    
    # Show recommendations
    if report["recommendations"]:
        print("\n💡 Security Recommendations:")
        for recommendation in report["recommendations"][:5]:
            print(f"   - {recommendation}")
    
    print("\n" + "=" * 50)
    
    if success:
        print("✅ PRODUCTION SECRETS VALIDATION PASSED")
        print("   Environment is ready for production deployment")
    else:
        print("❌ PRODUCTION SECRETS VALIDATION FAILED")
        print("   Fix security issues before production deployment")
    
    return success


def check_secret_requirements() -> bool:
    """Check that all required secrets are properly configured."""
    print("\n🔐 Checking Secret Requirements")
    print("-" * 30)
    
    # Check environment variables
    missing_secrets = []
    weak_secrets = []
    
    for requirement in infrastructure_security.SECRET_REQUIREMENTS:
        if requirement.required_in_production:
            value = os.getenv(requirement.name, "")
            
            if not value:
                missing_secrets.append(requirement.name)
                continue
            
            # Validate the secret
            issues = infrastructure_security.validate_secret(requirement, value)
            if issues:
                weak_secrets.append((requirement.name, issues))
    
    success = True
    
    if missing_secrets:
        print(f"❌ Missing required secrets: {', '.join(missing_secrets)}")
        success = False
    
    if weak_secrets:
        print(f"❌ Weak or invalid secrets found:")
        for secret_name, issues in weak_secrets:
            print(f"   {secret_name}: {', '.join(issues)}")
        success = False
    
    if success:
        print("✅ All required secrets are properly configured")
    
    return success


def main():
    """Main validation function."""
    print("🔒 Whisper Transcriber Production Security Validation")
    print("=" * 60)
    
    # Change to workspace root
    workspace_root = Path(__file__).parent.parent.parent
    os.chdir(workspace_root)
    
    all_checks_passed = True
    
    # Run all validation checks
    checks = [
        ("Production Secrets", validate_production_secrets),
        ("Secret Requirements", check_secret_requirements),
    ]
    
    for check_name, check_function in checks:
        try:
            result = check_function()
            if not result:
                all_checks_passed = False
        except Exception as e:
            print(f"❌ {check_name} check failed with error: {e}")
            all_checks_passed = False
    
    print("\n" + "=" * 60)
    
    if all_checks_passed:
        print("✅ ALL PRODUCTION SECURITY VALIDATIONS PASSED")
        print("   System is ready for production deployment")
        sys.exit(0)
    else:
        print("❌ PRODUCTION SECURITY VALIDATION FAILED")
        print("   Fix all security issues before deploying to production")
        sys.exit(1)


if __name__ == "__main__":
    main()