#!/usr/bin/env python3
"""
CI/CD Secret Scanner
Scans repository for hardcoded secrets and validates security configuration.
Designed to be run in CI/CD pipelines to prevent secret commits.
"""

import sys
import json
from pathlib import Path

# Add the API directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.security.infrastructure_security import infrastructure_security


def scan_secrets_for_ci() -> dict:
    """Scan for secrets and return results in CI-friendly format."""
    print("🔍 CI/CD Secret Scanning - Whisper Transcriber")
    print("=" * 55)
    
    results = {
        "status": "PASS",
        "hardcoded_secrets": [],
        "security_grade": "A",
        "issues": [],
        "recommendations": []
    }
    
    # Scan for hardcoded secrets
    print("📋 Scanning for hardcoded secrets...")
    hardcoded_secrets = infrastructure_security.scan_hardcoded_secrets()
    
    if hardcoded_secrets:
        results["status"] = "FAIL" 
        results["hardcoded_secrets"] = hardcoded_secrets
        results["issues"].append(f"Found {len(hardcoded_secrets)} hardcoded secrets")
        
        print(f"❌ Found {len(hardcoded_secrets)} hardcoded secrets:")
        for secret in hardcoded_secrets:
            print(f"   📁 {secret['file']}:{secret['line']} - {secret['type']} ({secret['severity']})")
    else:
        print("✅ No hardcoded secrets detected")
    
    # Generate comprehensive security report
    print("\n📊 Generating security assessment...")
    security_report = infrastructure_security.generate_security_report()
    
    results["security_grade"] = security_report["overall_security_grade"]
    results["recommendations"] = security_report["recommendations"]
    
    # Validate environment files
    print("\n🔧 Validating environment configuration...")
    env_files_checked = 0
    for env_file in [".env", ".env.development", ".env.production"]:
        env_path = Path(env_file)
        if env_path.exists():
            env_files_checked += 1
            validation = infrastructure_security.validate_environment(env_file)
            
            if not validation["valid"]:
                results["status"] = "FAIL"
                results["issues"].extend([
                    f"{env_file}: {error}" for error in validation["errors"]
                ])
                print(f"❌ {env_file}: {len(validation['errors'])} errors")
            else:
                print(f"✅ {env_file}: Validation passed (Score: {validation['security_score']}%)")
    
    if env_files_checked == 0:
        print("⚠️  No environment files found to validate")
    
    # Check for common security anti-patterns
    print("\n🛡️  Checking security anti-patterns...")
    security_issues = check_security_antipatterns()
    if security_issues:
        results["status"] = "FAIL"
        results["issues"].extend(security_issues)
        for issue in security_issues:
            print(f"❌ {issue}")
    else:
        print("✅ No security anti-patterns detected")
    
    # Summary
    print(f"\n📈 Security Grade: {results['security_grade']}")
    
    if results["status"] == "PASS":
        print("✅ CI/CD SECRET SCAN PASSED")
        print("   Repository is secure for deployment")
    else:
        print("❌ CI/CD SECRET SCAN FAILED")
        print(f"   Found {len(results['issues'])} security issues")
        print("   Review and fix issues before merging")
    
    return results


def check_security_antipatterns() -> list:
    """Check for common security anti-patterns in the codebase."""
    issues = []
    
    # Check for password in plain text
    suspicious_files = [
        "docker-compose.yml",
        "docker-compose.yaml", 
        ".env.example",
        "README.md"
    ]
    
    for file_path in suspicious_files:
        if Path(file_path).exists():
            try:
                with open(file_path, 'r') as f:
                    content = f.read().lower()
                    
                    # Check for suspicious patterns
                    if "password123" in content:
                        issues.append(f"{file_path} contains default password patterns")
                    
                    if "secret:" in content and "changeme" in content:
                        issues.append(f"{file_path} contains changeme secrets")
                    
                    if "admin:admin" in content:
                        issues.append(f"{file_path} contains admin:admin credentials")
                        
            except Exception:
                # Skip files that can't be read
                pass
    
    return issues


def generate_ci_report(results: dict) -> None:
    """Generate CI-friendly report formats."""
    
    # JSON report for automated processing
    json_report = {
        "scan_type": "security_secrets",
        "status": results["status"],
        "security_grade": results["security_grade"],
        "issues_count": len(results["issues"]),
        "secrets_count": len(results["hardcoded_secrets"]),
        "issues": results["issues"],
        "hardcoded_secrets": results["hardcoded_secrets"],
        "recommendations": results["recommendations"]
    }
    
    with open("security_scan_report.json", "w") as f:
        json.dump(json_report, f, indent=2)
    
    # Markdown report for pull requests
    markdown_report = generate_markdown_report(results)
    with open("security_scan_report.md", "w") as f:
        f.write(markdown_report)
    
    print(f"\n📄 Reports generated:")
    print(f"   📋 security_scan_report.json - Machine-readable results")
    print(f"   📝 security_scan_report.md - Human-readable summary")


def generate_markdown_report(results: dict) -> str:
    """Generate a markdown report for pull requests."""
    
    status_emoji = "✅" if results["status"] == "PASS" else "❌"
    grade_emoji = {
        "A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴", "F": "💀"
    }.get(results["security_grade"], "❓")
    
    report = f"""# {status_emoji} Security Scan Report

## Summary
- **Status**: {results["status"]}
- **Security Grade**: {grade_emoji} {results["security_grade"]}
- **Issues Found**: {len(results["issues"])}
- **Hardcoded Secrets**: {len(results["hardcoded_secrets"])}

"""
    
    if results["hardcoded_secrets"]:
        report += """## 🚨 Hardcoded Secrets Detected

The following hardcoded secrets were found and must be removed:

| File | Line | Type | Severity |
|------|------|------|----------|
"""
        for secret in results["hardcoded_secrets"]:
            report += f"| `{secret['file']}` | {secret['line']} | {secret['type']} | {secret['severity']} |\n"
        
        report += "\n"
    
    if results["issues"]:
        report += """## ⚠️ Security Issues

The following security issues were identified:

"""
        for issue in results["issues"]:
            report += f"- {issue}\n"
        
        report += "\n"
    
    if results["recommendations"]:
        report += """## 💡 Recommendations

To improve security posture:

"""
        for rec in results["recommendations"][:5]:  # Limit to top 5
            report += f"- {rec}\n"
        
        report += "\n"
    
    if results["status"] == "PASS":
        report += """## ✅ Scan Results

All security checks passed! The code is ready for deployment.

"""
    else:
        report += """## ❌ Action Required

Security issues were detected that must be resolved before merging:

1. Remove all hardcoded secrets and move to environment variables
2. Fix security configuration issues
3. Address anti-pattern violations
4. Re-run the security scan to verify fixes

"""
    
    return report


def main():
    """Main CI/CD scanning function."""
    # Change to repository root
    repo_root = Path(__file__).parent.parent
    import os
    os.chdir(repo_root)
    
    # Run the scan
    results = scan_secrets_for_ci()
    
    # Generate reports
    generate_ci_report(results)
    
    # Set exit code based on results
    if results["status"] == "PASS":
        print(f"\n🎉 Security scan completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 Security scan failed - fix issues before proceeding")
        sys.exit(1)


if __name__ == "__main__":
    main()