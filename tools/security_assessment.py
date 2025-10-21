#!/usr/bin/env python3
"""
T026 Security Assessment Tool

Comprehensive security audit of the Whisper Transcriber application to identify
vulnerabilities and security hardening opportunities across all components.
"""

import json
import subprocess
import time
import requests
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import re
import os

@dataclass
class SecurityFinding:
    """Security finding or vulnerability."""
    category: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    title: str
    description: str
    location: str
    recommendation: str
    cwe_id: str = None
    cvss_score: float = None


class SecurityAssessment:
    """Comprehensive security assessment tool."""
    
    def __init__(self):
        self.findings: List[SecurityFinding] = []
        self.project_root = Path.cwd()
        self.base_url = "http://localhost:8000"
    
    def add_finding(self, category: str, severity: str, title: str, 
                   description: str, location: str, recommendation: str, 
                   cwe_id: str = None, cvss_score: float = None):
        """Add a security finding."""
        finding = SecurityFinding(
            category=category,
            severity=severity,
            title=title,
            description=description,
            location=location,
            recommendation=recommendation,
            cwe_id=cwe_id,
            cvss_score=cvss_score
        )
        self.findings.append(finding)
        print(f"🔍 {severity}: {title} ({location})")
    
    def assess_authentication_security(self):
        """Assess authentication and authorization security."""
        print("🔐 Assessing authentication security...")
        
        # Check JWT implementation
        auth_file = self.project_root / "api" / "routes" / "auth.py"
        if auth_file.exists():
            content = auth_file.read_text()
            
            # Check for hardcoded secrets
            if "secret" in content.lower() and ("test" in content.lower() or "example" in content.lower()):
                self.add_finding(
                    "Authentication",
                    "MEDIUM",
                    "Potential hardcoded secrets in auth.py",
                    "Authentication file may contain hardcoded test secrets",
                    "api/routes/auth.py",
                    "Use environment variables for all secrets and remove test credentials",
                    "CWE-798"
                )
            
            # Check password hashing
            if "bcrypt" not in content and "scrypt" not in content and "pbkdf2" not in content:
                self.add_finding(
                    "Authentication",
                    "HIGH",
                    "Weak password hashing detected",
                    "Password hashing implementation may be using weak algorithms",
                    "api/routes/auth.py",
                    "Implement bcrypt, scrypt, or PBKDF2 for password hashing",
                    "CWE-916"
                )
            
            # Check for password complexity requirements
            if "password.*length" not in content.lower() and "len.*password" not in content.lower():
                self.add_finding(
                    "Authentication",
                    "MEDIUM",
                    "No password complexity validation",
                    "Password complexity requirements not enforced",
                    "api/routes/auth.py",
                    "Implement password length, complexity, and strength requirements",
                    "CWE-521"
                )
        
        # Check JWT token configuration
        settings_file = self.project_root / "api" / "settings.py"
        if settings_file.exists():
            content = settings_file.read_text()
            
            # Check JWT expiration
            if "access_token_expire" not in content.lower():
                self.add_finding(
                    "Authentication",
                    "MEDIUM",
                    "JWT token expiration not configured",
                    "Access tokens may not have appropriate expiration times",
                    "api/settings.py",
                    "Configure appropriate JWT token expiration (15-60 minutes)",
                    "CWE-613"
                )
    
    def assess_api_security(self):
        """Assess API endpoint security."""
        print("🌐 Assessing API security...")
        
        # Check for rate limiting
        rate_limit_found = False
        for py_file in self.project_root.glob("api/**/*.py"):
            content = py_file.read_text()
            if "rate" in content.lower() and "limit" in content.lower():
                rate_limit_found = True
                break
        
        if not rate_limit_found:
            self.add_finding(
                "API Security",
                "HIGH",
                "No rate limiting implemented",
                "API endpoints lack rate limiting protection against abuse",
                "api/**/*.py",
                "Implement rate limiting with Redis backend for all endpoints",
                "CWE-770",
                7.5
            )
        
        # Check CORS configuration
        main_file = self.project_root / "api" / "main.py"
        if main_file.exists():
            content = main_file.read_text()
            
            # Check for overly permissive CORS
            if "allow_origins.*\\*" in content or "allow_origins=[\"*\"]" in content:
                self.add_finding(
                    "API Security",
                    "MEDIUM",
                    "Overly permissive CORS configuration",
                    "CORS allows all origins which may be unsafe for production",
                    "api/main.py",
                    "Configure specific allowed origins for production environment",
                    "CWE-942"
                )
            
            # Check for security headers
            if "security" not in content.lower() or "header" not in content.lower():
                self.add_finding(
                    "API Security",
                    "MEDIUM",
                    "Missing security headers",
                    "Application lacks security headers (CSP, HSTS, X-Frame-Options)",
                    "api/main.py",
                    "Implement comprehensive security headers middleware",
                    "CWE-693"
                )
    
    def assess_input_validation(self):
        """Assess input validation and sanitization."""
        print("🛡️ Assessing input validation...")
        
        # Check for SQL injection protection
        db_files = list(self.project_root.glob("api/**/*.py"))
        sql_injection_protection = False
        
        for db_file in db_files:
            content = db_file.read_text()
            if "sqlalchemy" in content.lower() and ("query" in content.lower() or "execute" in content.lower()):
                # Check for parameterized queries
                if "text(" in content and "%" in content:
                    self.add_finding(
                        "Input Validation",
                        "CRITICAL",
                        "Potential SQL injection vulnerability",
                        f"Raw SQL queries detected in {db_file.name}",
                        str(db_file),
                        "Use parameterized queries and ORM methods exclusively",
                        "CWE-89",
                        9.3
                    )
                else:
                    sql_injection_protection = True
        
        # Check for file upload validation
        upload_files = []
        for py_file in self.project_root.glob("api/**/*.py"):
            content = py_file.read_text()
            if "upload" in content.lower() and ("file" in content.lower() or "chunk" in content.lower()):
                upload_files.append(py_file)
        
        for upload_file in upload_files:
            content = upload_file.read_text()
            
            # Check file type validation
            if "content-type" not in content.lower() and "mimetype" not in content.lower():
                self.add_finding(
                    "Input Validation",
                    "HIGH",
                    "Insufficient file upload validation",
                    f"File uploads in {upload_file.name} lack content type validation",
                    str(upload_file),
                    "Implement strict file type validation and content scanning",
                    "CWE-434",
                    8.1
                )
            
            # Check file size limits
            if "size" not in content.lower() or "limit" not in content.lower():
                self.add_finding(
                    "Input Validation",
                    "MEDIUM",
                    "Missing file size validation",
                    f"File uploads in {upload_file.name} may lack size limits",
                    str(upload_file),
                    "Implement strict file size limits and validation",
                    "CWE-770"
                )
    
    def assess_dependency_security(self):
        """Assess dependency and package security."""
        print("📦 Assessing dependency security...")
        
        # Check requirements for known vulnerabilities
        req_files = ["requirements.txt", "requirements-dev.txt", "pyproject.toml"]
        
        for req_file in req_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                # Check for outdated or vulnerable packages
                content = req_path.read_text()
                
                # Common vulnerable patterns
                vulnerable_patterns = [
                    (r"django<3\.2", "Django version may be vulnerable"),
                    (r"flask<2\.0", "Flask version may be vulnerable"),
                    (r"requests<2\.25", "Requests version may be vulnerable"),
                    (r"pyyaml<5\.4", "PyYAML version may be vulnerable"),
                    (r"pillow<8\.3", "Pillow version may be vulnerable")
                ]
                
                for pattern, description in vulnerable_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        self.add_finding(
                            "Dependencies",
                            "HIGH",
                            "Potentially vulnerable dependency",
                            description,
                            str(req_path),
                            "Update to latest secure versions of dependencies",
                            "CWE-1104"
                        )
    
    def assess_file_system_security(self):
        """Assess file system security."""
        print("📁 Assessing file system security...")
        
        # Check for sensitive files
        sensitive_patterns = [
            "*.key", "*.pem", "*.p12", "*.pfx",
            ".env", "*.secret", "config.json"
        ]
        
        for pattern in sensitive_patterns:
            for sensitive_file in self.project_root.glob(f"**/{pattern}"):
                if sensitive_file.is_file():
                    # Check if file is in version control
                    gitignore = self.project_root / ".gitignore"
                    if gitignore.exists():
                        gitignore_content = gitignore.read_text()
                        if sensitive_file.name not in gitignore_content:
                            self.add_finding(
                                "File System",
                                "HIGH",
                                "Sensitive file not in .gitignore",
                                f"Sensitive file {sensitive_file.name} may be committed to version control",
                                str(sensitive_file),
                                f"Add {sensitive_file.name} to .gitignore",
                                "CWE-200"
                            )
        
        # Check directory permissions
        critical_dirs = ["uploads", "storage", "logs", "backups"]
        for dir_name in critical_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                # Check if directory is web-accessible
                if (dir_path / "index.html").exists() or (dir_path / ".htaccess").exists():
                    continue  # Has protection
                else:
                    self.add_finding(
                        "File System",
                        "MEDIUM",
                        "Directory lacks access protection",
                        f"Directory {dir_name} may be web-accessible",
                        str(dir_path),
                        "Add index.html or .htaccess to prevent directory listing",
                        "CWE-200"
                    )
    
    def assess_logging_security(self):
        """Assess logging and monitoring security."""
        print("📝 Assessing logging security...")
        
        # Check for audit logging
        audit_logging_found = False
        for py_file in self.project_root.glob("api/**/*.py"):
            content = py_file.read_text()
            if "audit" in content.lower() and "log" in content.lower():
                audit_logging_found = True
                break
        
        if not audit_logging_found:
            self.add_finding(
                "Logging",
                "MEDIUM",
                "No audit logging implemented",
                "Application lacks comprehensive audit logging for security events",
                "api/**/*.py",
                "Implement audit logging for authentication, authorization, and sensitive operations",
                "CWE-778"
            )
        
        # Check for log injection protection
        for py_file in self.project_root.glob("api/**/*.py"):
            content = py_file.read_text()
            if "log" in content.lower() and ("format" in content.lower() or "%" in content or ".format(" in content):
                if "user" in content.lower() or "request" in content.lower():
                    self.add_finding(
                        "Logging",
                        "MEDIUM",
                        "Potential log injection vulnerability",
                        f"User input may be logged without sanitization in {py_file.name}",
                        str(py_file),
                        "Sanitize user input before logging to prevent log injection",
                        "CWE-117"
                    )
    
    def assess_configuration_security(self):
        """Assess configuration security."""
        print("⚙️ Assessing configuration security...")
        
        # Check environment configuration
        env_files = [".env", ".env.example", ".env.prod"]
        
        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                content = env_path.read_text()
                
                # Check for debug mode in production
                if "debug.*true" in content.lower() or "development" in content.lower():
                    if "prod" in env_file:
                        self.add_finding(
                            "Configuration",
                            "HIGH",
                            "Debug mode enabled in production",
                            f"Debug mode may be enabled in {env_file}",
                            str(env_path),
                            "Disable debug mode in production environment",
                            "CWE-489"
                        )
                
                # Check for weak secrets
                secret_patterns = [
                    (r"secret.*=.*test", "Test secret in configuration"),
                    (r"password.*=.*password", "Default password in configuration"),
                    (r"key.*=.*123", "Weak key in configuration")
                ]
                
                for pattern, description in secret_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        self.add_finding(
                            "Configuration",
                            "HIGH",
                            "Weak secret configuration",
                            description,
                            str(env_path),
                            "Use strong, randomly generated secrets",
                            "CWE-798"
                        )
    
    def test_live_endpoints(self):
        """Test live endpoints for security issues."""
        print("🌐 Testing live endpoint security...")
        
        try:
            # Test for information disclosure
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                # Check response headers for security
                headers = response.headers
                
                security_headers = [
                    "X-Content-Type-Options",
                    "X-Frame-Options", 
                    "X-XSS-Protection",
                    "Strict-Transport-Security",
                    "Content-Security-Policy"
                ]
                
                missing_headers = [h for h in security_headers if h not in headers]
                if missing_headers:
                    self.add_finding(
                        "HTTP Headers",
                        "MEDIUM",
                        "Missing security headers",
                        f"Missing headers: {', '.join(missing_headers)}",
                        "HTTP Response",
                        "Implement missing security headers",
                        "CWE-693"
                    )
                
                # Check for server information disclosure
                if "Server" in headers and ("apache" in headers["Server"].lower() or "nginx" in headers["Server"].lower()):
                    self.add_finding(
                        "Information Disclosure",
                        "LOW",
                        "Server information disclosure",
                        f"Server header reveals: {headers['Server']}",
                        "HTTP Response",
                        "Remove or obfuscate server header",
                        "CWE-200"
                    )
        
        except Exception as e:
            print(f"Note: Could not test live endpoints: {e}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive security assessment report."""
        # Categorize findings by severity
        critical = [f for f in self.findings if f.severity == "CRITICAL"]
        high = [f for f in self.findings if f.severity == "HIGH"]
        medium = [f for f in self.findings if f.severity == "MEDIUM"]
        low = [f for f in self.findings if f.severity == "LOW"]
        info = [f for f in self.findings if f.severity == "INFO"]
        
        # Calculate risk score
        risk_score = (len(critical) * 10) + (len(high) * 7) + (len(medium) * 4) + (len(low) * 1)
        max_possible = len(self.findings) * 10
        risk_percentage = (risk_score / max_possible * 100) if max_possible > 0 else 0
        
        # Determine overall security rating
        if risk_percentage >= 70:
            security_rating = "CRITICAL"
        elif risk_percentage >= 50:
            security_rating = "HIGH RISK"
        elif risk_percentage >= 30:
            security_rating = "MEDIUM RISK"
        elif risk_percentage >= 10:
            security_rating = "LOW RISK"
        else:
            security_rating = "SECURE"
        
        report = {
            "assessment_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_findings": len(self.findings),
            "security_rating": security_rating,
            "risk_score": risk_score,
            "risk_percentage": risk_percentage,
            "findings_by_severity": {
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium),
                "low": len(low),
                "info": len(info)
            },
            "top_priorities": [asdict(f) for f in critical + high[:5]],
            "all_findings": [asdict(f) for f in self.findings],
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate prioritized security recommendations."""
        recommendations = [
            "Implement comprehensive rate limiting for all API endpoints",
            "Add audit logging for all security-sensitive operations", 
            "Enhance input validation and sanitization across all endpoints",
            "Implement security headers (CSP, HSTS, X-Frame-Options)",
            "Add CSRF protection for state-changing operations",
            "Implement API key management system with role-based access",
            "Add vulnerability scanning to CI/CD pipeline",
            "Create incident response procedures and security documentation",
            "Implement security monitoring and alerting",
            "Conduct regular penetration testing and security audits"
        ]
        
        # Prioritize based on findings
        critical_areas = set()
        for finding in self.findings:
            if finding.severity in ["CRITICAL", "HIGH"]:
                critical_areas.add(finding.category)
        
        # Reorder recommendations based on critical areas found
        prioritized = []
        for rec in recommendations:
            if any(area.lower() in rec.lower() for area in critical_areas):
                prioritized.insert(0, rec)
            else:
                prioritized.append(rec)
        
        return prioritized[:10]  # Top 10 recommendations
    
    def run_assessment(self) -> Dict[str, Any]:
        """Run comprehensive security assessment."""
        print("🔒 Starting T026 Security Assessment...")
        print("=" * 50)
        
        # Run all assessment modules
        self.assess_authentication_security()
        self.assess_api_security()
        self.assess_input_validation()
        self.assess_dependency_security()
        self.assess_file_system_security()
        self.assess_logging_security()
        self.assess_configuration_security()
        self.test_live_endpoints()
        
        # Generate report
        report = self.generate_report()
        
        # Print summary
        print(f"\n{'='*50}")
        print(f"🔍 SECURITY ASSESSMENT COMPLETE")
        print(f"{'='*50}")
        print(f"Security Rating: {report['security_rating']}")
        print(f"Total Findings: {report['total_findings']}")
        print(f"Risk Score: {report['risk_score']}/100")
        
        severity_counts = report['findings_by_severity']
        if severity_counts['critical'] > 0:
            print(f"🚨 Critical: {severity_counts['critical']}")
        if severity_counts['high'] > 0:
            print(f"⚠️  High: {severity_counts['high']}")
        if severity_counts['medium'] > 0:
            print(f"🟡 Medium: {severity_counts['medium']}")
        if severity_counts['low'] > 0:
            print(f"ℹ️  Low: {severity_counts['low']}")
        
        print(f"\n🎯 Top Priority Recommendations:")
        for i, rec in enumerate(report['recommendations'][:5], 1):
            print(f"   {i}. {rec}")
        
        return report


def main():
    """Run the security assessment."""
    assessment = SecurityAssessment()
    report = assessment.run_assessment()
    
    # Save report
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = Path(f"temp/T026_Security_Assessment_{timestamp}.json")
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Return appropriate exit code based on findings
    critical_high = report['findings_by_severity']['critical'] + report['findings_by_severity']['high']
    if critical_high > 5:
        return 2  # Critical security issues
    elif critical_high > 0:
        return 1  # Some security issues
    else:
        return 0  # No critical issues


if __name__ == "__main__":
    exit(main())
