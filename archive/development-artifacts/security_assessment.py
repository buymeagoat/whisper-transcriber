#!/usr/bin/env python3
"""
T026 Security Assessment Script

Comprehensive security audit for the whisper-transcriber application.
Identifies vulnerabilities, security issues, and compliance gaps.
"""

import os
import re
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class SecurityAssessment:
    """Comprehensive security assessment tool."""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.findings = []
        self.risk_score = 0
        
    def add_finding(self, severity: str, category: str, title: str, description: str, 
                   file_path: str = None, line_number: int = None, recommendation: str = None):
        """Add a security finding."""
        finding = {
            "severity": severity,
            "category": category,
            "title": title,
            "description": description,
            "file_path": file_path,
            "line_number": line_number,
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat()
        }
        self.findings.append(finding)
        
        # Add to risk score
        severity_scores = {"CRITICAL": 25, "HIGH": 10, "MEDIUM": 5, "LOW": 2, "INFO": 1}
        self.risk_score += severity_scores.get(severity, 0)
        
        print(f"[{severity}] {category}: {title}")
        if file_path:
            print(f"  File: {file_path}:{line_number or 'N/A'}")
        print(f"  Description: {description}")
        if recommendation:
            print(f"  Recommendation: {recommendation}")
        print()
    
    def scan_sql_injection_vulnerabilities(self):
        """Scan for SQL injection vulnerabilities."""
        print("🔍 Scanning for SQL injection vulnerabilities...")
        
        # Patterns that indicate potential SQL injection
        sql_patterns = [
            r'execute\s*\(\s*["\'].*\%.*["\']',  # String formatting in SQL
            r'execute\s*\(\s*f["\'].*\{.*\}.*["\']',  # f-strings in SQL
            r'execute\s*\(\s*.*\+.*\)',  # String concatenation in SQL
            r'\.format\s*\(.*\).*execute',  # .format() with execute
            r'cursor\.execute\s*\(\s*["\'].*\%',  # Direct string formatting
            r'query\s*=.*\%.*execute'  # Query with string formatting
        ]
        
        # Scan Python files
        python_files = list(self.project_root.glob("**/*.py"))
        for file_path in python_files:
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue
                
            try:
                content = file_path.read_text()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern in sql_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            self.add_finding(
                                "CRITICAL",
                                "SQL Injection",
                                "Potential SQL injection vulnerability",
                                f"Unsafe SQL query construction detected: {line.strip()}",
                                str(file_path.relative_to(self.project_root)),
                                line_num,
                                "Use parameterized queries or ORM methods instead of string formatting"
                            )
                            
                    # Check for raw SQL queries
                    if re.search(r'execute\s*\(\s*["\'][^"\']*["\']', line, re.IGNORECASE):
                        if "%" in line or ".format" in line or "{" in line:
                            continue  # Already caught above
                        # Check if it's a raw query with potential user input
                        if any(param in line.lower() for param in ['input', 'request', 'form', 'json', 'args']):
                            self.add_finding(
                                "HIGH",
                                "SQL Injection",
                                "Raw SQL query with potential user input",
                                f"Raw SQL query may be vulnerable: {line.strip()}",
                                str(file_path.relative_to(self.project_root)),
                                line_num,
                                "Review and ensure proper parameterization"
                            )
            except Exception as e:
                print(f"Error scanning {file_path}: {e}")
    
    def scan_authentication_issues(self):
        """Scan for authentication and authorization issues."""
        print("🔍 Scanning for authentication issues...")
        
        # Check for hardcoded secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']{4,}["\']',
            r'secret\s*=\s*["\'][^"\']{10,}["\']',
            r'key\s*=\s*["\'][^"\']{10,}["\']',
            r'token\s*=\s*["\'][^"\']{10,}["\']',
            r'api_key\s*=\s*["\'][^"\']{10,}["\']'
        ]
        
        python_files = list(self.project_root.glob("**/*.py"))
        for file_path in python_files:
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue
                
            try:
                content = file_path.read_text()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern in secret_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Skip obvious test/example values
                            if any(test_val in line.lower() for test_val in ['test', 'example', 'fake', 'demo', 'placeholder']):
                                continue
                            self.add_finding(
                                "HIGH",
                                "Authentication",
                                "Hardcoded secret detected",
                                f"Potential hardcoded secret: {line.strip()}",
                                str(file_path.relative_to(self.project_root)),
                                line_num,
                                "Move secrets to environment variables or secure configuration"
                            )
                    
                    # Check for weak password hashing
                    if re.search(r'md5|sha1(?!hashlib)|sha256(?!hashlib)', line, re.IGNORECASE):
                        if 'password' in line.lower():
                            self.add_finding(
                                "HIGH",
                                "Authentication",
                                "Weak password hashing",
                                f"Weak hashing algorithm for passwords: {line.strip()}",
                                str(file_path.relative_to(self.project_root)),
                                line_num,
                                "Use bcrypt, scrypt, or Argon2 for password hashing"
                            )
                    
                    # Check for JWT without expiration
                    if 'jwt.encode' in line and 'exp' not in line:
                        self.add_finding(
                            "MEDIUM",
                            "Authentication",
                            "JWT without expiration",
                            f"JWT token may not have expiration set: {line.strip()}",
                            str(file_path.relative_to(self.project_root)),
                            line_num,
                            "Always set JWT expiration time"
                        )
                        
            except Exception as e:
                print(f"Error scanning {file_path}: {e}")
    
    def scan_file_upload_vulnerabilities(self):
        """Scan for file upload security issues."""
        print("🔍 Scanning for file upload vulnerabilities...")
        
        upload_files = []
        for file_path in self.project_root.glob("**/*.py"):
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue
                
            try:
                content = file_path.read_text()
                if any(keyword in content.lower() for keyword in ['upload', 'file', 'multipart']):
                    upload_files.append(file_path)
            except:
                continue
        
        for file_path in upload_files:
            try:
                content = file_path.read_text()
                lines = content.split('\n')
                
                has_size_check = False
                has_type_check = False
                has_extension_check = False
                
                for line_num, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    
                    # Check for file size validation
                    if any(keyword in line_lower for keyword in ['size', 'length', 'content-length']):
                        if any(op in line for op in ['>', '<', '>=', '<=', 'max', 'limit']):
                            has_size_check = True
                    
                    # Check for content type validation
                    if any(keyword in line_lower for keyword in ['content-type', 'content_type', 'mimetype']):
                        has_type_check = True
                    
                    # Check for file extension validation
                    if any(keyword in line_lower for keyword in ['extension', 'suffix', 'endswith']):
                        has_extension_check = True
                    
                    # Check for dangerous file operations
                    if 'open(' in line and any(mode in line for mode in ['w', 'a', 'x']):
                        if not any(safe in line_lower for safe in ['safe', 'sanitize', 'validate']):
                            self.add_finding(
                                "MEDIUM",
                                "File Upload",
                                "Potentially unsafe file operation",
                                f"File operation without apparent validation: {line.strip()}",
                                str(file_path.relative_to(self.project_root)),
                                line_num,
                                "Ensure file paths are validated and sanitized"
                            )
                
                # Check if upload file lacks proper validation
                if 'upload' in content.lower():
                    if not has_size_check:
                        self.add_finding(
                            "MEDIUM",
                            "File Upload",
                            "Missing file size validation",
                            "File upload endpoint may not validate file size",
                            str(file_path.relative_to(self.project_root)),
                            None,
                            "Implement file size limits to prevent DoS attacks"
                        )
                    
                    if not has_type_check:
                        self.add_finding(
                            "MEDIUM",
                            "File Upload",
                            "Missing content type validation",
                            "File upload endpoint may not validate content type",
                            str(file_path.relative_to(self.project_root)),
                            None,
                            "Validate file content types to prevent malicious uploads"
                        )
                        
            except Exception as e:
                print(f"Error scanning {file_path}: {e}")
    
    def scan_logging_vulnerabilities(self):
        """Scan for log injection vulnerabilities."""
        print("🔍 Scanning for log injection vulnerabilities...")
        
        python_files = list(self.project_root.glob("**/*.py"))
        for file_path in python_files:
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue
                
            try:
                content = file_path.read_text()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    # Check for logging with user input
                    if any(log_func in line.lower() for log_func in ['log.', 'logger.', 'logging.', 'print(']):
                        if any(user_input in line.lower() for user_input in ['request', 'input', 'user', 'form', 'json']):
                            if not any(safe in line.lower() for safe in ['escape', 'sanitize', 'safe', 'repr(']):
                                self.add_finding(
                                    "MEDIUM",
                                    "Log Injection",
                                    "Potential log injection vulnerability",
                                    f"User input in logging without sanitization: {line.strip()}",
                                    str(file_path.relative_to(self.project_root)),
                                    line_num,
                                    "Sanitize user input before logging or use structured logging"
                                )
                                
            except Exception as e:
                print(f"Error scanning {file_path}: {e}")
    
    def scan_security_headers(self):
        """Check for security headers implementation."""
        print("🔍 Checking security headers...")
        
        # Check for security headers in main application files
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Strict-Transport-Security',
            'Content-Security-Policy'
        ]
        
        found_headers = set()
        
        for file_path in self.project_root.glob("**/*.py"):
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue
                
            try:
                content = file_path.read_text()
                for header in security_headers:
                    if header in content:
                        found_headers.add(header)
            except:
                continue
        
        missing_headers = set(security_headers) - found_headers
        for header in missing_headers:
            self.add_finding(
                "MEDIUM",
                "Security Headers",
                f"Missing security header: {header}",
                f"Security header {header} not implemented",
                None,
                None,
                f"Implement {header} header to improve security posture"
            )
    
    def scan_dependency_vulnerabilities(self):
        """Check for dependency vulnerabilities."""
        print("🔍 Scanning dependency vulnerabilities...")
        
        # Check requirements files
        req_files = ['requirements.txt', 'requirements-dev.txt', 'pyproject.toml']
        
        for req_file in req_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                try:
                    content = req_path.read_text()
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Check for unpinned dependencies
                            if '==' not in line and '>=' not in line and '~=' not in line:
                                if any(char in line for char in ['>', '<', '!']):
                                    continue  # Has some version constraint
                                self.add_finding(
                                    "LOW",
                                    "Dependencies",
                                    "Unpinned dependency",
                                    f"Dependency without version pinning: {line}",
                                    req_file,
                                    line_num,
                                    "Pin dependency versions for reproducible builds"
                                )
                                
                except Exception as e:
                    print(f"Error reading {req_file}: {e}")
    
    def scan_file_permissions(self):
        """Check file and directory permissions."""
        print("🔍 Checking file permissions...")
        
        # Check for world-writable files
        sensitive_dirs = ['uploads', 'storage', 'logs', 'cache', 'backups']
        
        for dir_name in sensitive_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                try:
                    # Check directory permissions
                    stat_info = dir_path.stat()
                    mode = stat_info.st_mode & 0o777
                    
                    if mode & 0o002:  # World writable
                        self.add_finding(
                            "MEDIUM",
                            "File Permissions",
                            "World-writable directory",
                            f"Directory {dir_name} is world-writable",
                            str(dir_path.relative_to(self.project_root)),
                            None,
                            "Restrict directory permissions to prevent unauthorized access"
                        )
                        
                except Exception as e:
                    print(f"Error checking permissions for {dir_path}: {e}")
    
    def scan_configuration_security(self):
        """Check configuration security."""
        print("🔍 Checking configuration security...")
        
        # Check .env files
        env_files = ['.env', '.env.local', '.env.production', '.env.development']
        
        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                try:
                    content = env_path.read_text()
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Check for weak secrets
                            if any(keyword in line.upper() for keyword in ['SECRET', 'KEY', 'PASSWORD', 'TOKEN']):
                                value = line.split('=', 1)[1] if '=' in line else ''
                                if len(value) < 16:
                                    self.add_finding(
                                        "MEDIUM",
                                        "Configuration",
                                        "Weak secret in configuration",
                                        f"Short secret value detected in {env_file}",
                                        env_file,
                                        line_num,
                                        "Use strong, randomly generated secrets (16+ characters)"
                                    )
                                
                except Exception as e:
                    print(f"Error reading {env_file}: {e}")
        
        # Check if .env is in .gitignore
        gitignore_path = self.project_root / '.gitignore'
        if gitignore_path.exists():
            try:
                gitignore_content = gitignore_path.read_text()
                if '.env' not in gitignore_content:
                    self.add_finding(
                        "HIGH",
                        "Configuration",
                        ".env file not in .gitignore",
                        "Environment file with secrets may be committed to version control",
                        ".gitignore",
                        None,
                        "Add .env files to .gitignore to prevent secret exposure"
                    )
            except Exception as e:
                print(f"Error reading .gitignore: {e}")
    
    def scan_api_security(self):
        """Check API security issues."""
        print("🔍 Checking API security...")
        
        # Check for rate limiting
        has_rate_limiting = False
        
        for file_path in self.project_root.glob("**/*.py"):
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue
                
            try:
                content = file_path.read_text()
                if any(keyword in content.lower() for keyword in ['rate_limit', 'ratelimit', 'slowapi', 'limiter']):
                    has_rate_limiting = True
                    break
            except:
                continue
        
        if not has_rate_limiting:
            self.add_finding(
                "HIGH",
                "API Security",
                "No rate limiting implemented",
                "API endpoints lack rate limiting protection",
                None,
                None,
                "Implement rate limiting to prevent abuse and DoS attacks"
            )
        
        # Check for CORS configuration
        has_cors = False
        for file_path in self.project_root.glob("**/*.py"):
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue
                
            try:
                content = file_path.read_text()
                if 'CORS' in content or 'cors' in content.lower():
                    has_cors = True
                    break
            except:
                continue
        
        if not has_cors:
            self.add_finding(
                "MEDIUM",
                "API Security",
                "CORS configuration not found",
                "No CORS configuration detected",
                None,
                None,
                "Configure CORS properly to control cross-origin requests"
            )
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        # Categorize findings
        categories = {}
        severities = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        
        for finding in self.findings:
            category = finding["category"]
            severity = finding["severity"]
            
            if category not in categories:
                categories[category] = []
            categories[category].append(finding)
            severities[severity] += 1
        
        # Calculate security rating
        if self.risk_score <= 20:
            security_rating = "LOW RISK"
        elif self.risk_score <= 50:
            security_rating = "MEDIUM RISK"
        elif self.risk_score <= 100:
            security_rating = "HIGH RISK"
        else:
            security_rating = "CRITICAL RISK"
        
        report = {
            "assessment_date": datetime.now().isoformat(),
            "security_rating": security_rating,
            "risk_score": self.risk_score,
            "total_findings": len(self.findings),
            "severity_breakdown": severities,
            "categories": list(categories.keys()),
            "findings_by_category": categories,
            "all_findings": self.findings,
            "recommendations": self._get_recommendations()
        }
        
        return report
    
    def _get_recommendations(self) -> List[str]:
        """Get prioritized security recommendations."""
        recommendations = []
        
        # Critical recommendations
        critical_findings = [f for f in self.findings if f["severity"] == "CRITICAL"]
        if critical_findings:
            recommendations.append("PRIORITY 1: Fix all CRITICAL security vulnerabilities immediately")
        
        # High priority recommendations
        high_findings = [f for f in self.findings if f["severity"] == "HIGH"]
        if high_findings:
            recommendations.append("PRIORITY 2: Address HIGH severity security issues")
        
        # Common recommendations based on findings
        categories = {f["category"] for f in self.findings}
        
        if "SQL Injection" in categories:
            recommendations.append("Implement parameterized queries and prepared statements")
        
        if "Authentication" in categories:
            recommendations.append("Strengthen authentication security (bcrypt, JWT expiration, secrets)")
        
        if "File Upload" in categories:
            recommendations.append("Implement comprehensive file upload validation")
        
        if "API Security" in categories:
            recommendations.append("Add rate limiting and API security measures")
        
        if "Security Headers" in categories:
            recommendations.append("Implement security headers middleware")
        
        return recommendations
    
    def run_assessment(self) -> Dict[str, Any]:
        """Run comprehensive security assessment."""
        print("🔒 Starting T026 Security Assessment...")
        print("=" * 50)
        
        # Run all security scans
        self.scan_sql_injection_vulnerabilities()
        self.scan_authentication_issues()
        self.scan_file_upload_vulnerabilities()
        self.scan_logging_vulnerabilities()
        self.scan_security_headers()
        self.scan_dependency_vulnerabilities()
        self.scan_file_permissions()
        self.scan_configuration_security()
        self.scan_api_security()
        
        # Generate report
        report = self.generate_security_report()
        
        # Print summary
        print("=" * 50)
        print("🔒 SECURITY ASSESSMENT COMPLETE")
        print("=" * 50)
        print(f"Security Rating: {report['security_rating']}")
        print(f"Risk Score: {report['risk_score']}/100")
        print(f"Total Findings: {report['total_findings']}")
        print()
        print("Severity Breakdown:")
        for severity, count in report['severity_breakdown'].items():
            if count > 0:
                print(f"  {severity}: {count}")
        print()
        print("Categories Found:")
        for category in report['categories']:
            count = len(report['findings_by_category'][category])
            print(f"  {category}: {count} findings")
        
        return report


def main():
    """Run security assessment."""
    assessment = SecurityAssessment()
    report = assessment.run_assessment()
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = Path(f"temp/T026_Security_Assessment_{timestamp}.json")
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed security report saved to: {report_file}")
    
    # Return appropriate exit code
    if report["security_rating"] in ["CRITICAL RISK"]:
        return 2
    elif report["security_rating"] in ["HIGH RISK"]:
        return 1
    else:
        return 0


if __name__ == "__main__":
    exit(main())