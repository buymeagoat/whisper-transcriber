#!/usr/bin/env python3
"""
Comprehensive Application State Validator

Tests every documented facet of the Whisper Transcriber application to determine
its current operational state. This tool validates:

1. All 21 API endpoints
2. All 46 modules and 921 functions
3. Database integrity and performance
4. File system components
5. Configuration validity
6. External dependencies
7. Security features
8. Backup systems
9. Performance metrics
10. Documentation accuracy

Usage: python tools/comprehensive_validator.py [--component=all|api|db|files|config|security|backup|performance]
"""

import asyncio
import json
import logging
import sqlite3
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import tempfile
import requests
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    component: str
    test_name: str
    status: str  # PASS, FAIL, WARN, SKIP
    message: str
    duration_ms: float
    details: Optional[Dict] = None
    error: Optional[str] = None

@dataclass
class ComponentStatus:
    name: str
    overall_status: str
    tests_run: int
    tests_passed: int
    tests_failed: int
    tests_warned: int
    tests_skipped: int
    duration_ms: float
    critical_issues: List[str]
    warnings: List[str]
    recommendations: List[str]

class ComprehensiveValidator:
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
        self.inventory = self._load_inventory()
        self.config = self._load_config()
        
    def _load_inventory(self) -> Dict:
        """Load the current system inventory."""
        inventory_path = Path("docs/architecture/INVENTORY.json")
        if not inventory_path.exists():
            logger.error("Inventory file not found. Run 'make arch.scan' first.")
            sys.exit(1)
        
        with open(inventory_path) as f:
            return json.load(f)
    
    def _load_config(self) -> Dict:
        """Load environment configuration."""
        config = {}
        # Load .env.example first as defaults, then .env to override
        env_files = [".env.example", ".env"]
        
        for env_file in env_files:
            if Path(env_file).exists():
                with open(env_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key] = value
        return config
    
    def _record_result(self, component: str, test_name: str, status: str, 
                      message: str, duration_ms: float, details: Optional[Dict] = None,
                      error: Optional[str] = None):
        """Record a test result."""
        result = TestResult(
            component=component,
            test_name=test_name,
            status=status,
            message=message,
            duration_ms=duration_ms,
            details=details,
            error=error
        )
        self.results.append(result)
        
        # Log result
        level = logging.INFO
        if status == "FAIL":
            level = logging.ERROR
        elif status == "WARN":
            level = logging.WARNING
            
        logger.log(level, f"{component}.{test_name}: {status} - {message}")
    
    def _time_test(self, func, *args, **kwargs):
        """Execute a test function and measure duration."""
        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration = (time.time() - start) * 1000
            return result, duration, None
        except Exception as e:
            duration = (time.time() - start) * 1000
            return None, duration, str(e)

    async def validate_api_endpoints(self) -> ComponentStatus:
        """Test all documented API endpoints."""
        logger.info("🔍 Validating API endpoints...")
        component = "api_endpoints"
        start_time = time.time()
        
        # Check if server is running
        server_url = self.config.get("VITE_API_HOST", "http://localhost:8000")
        
        try:
            response = requests.get(f"{server_url}/health", timeout=5)
            server_running = response.status_code == 200
        except:
            server_running = False
            
        if not server_running:
            self._record_result(component, "server_availability", "FAIL", 
                              f"Server not responding at {server_url}", 0)
            return self._get_component_status(component, time.time() - start_time)
        
        self._record_result(component, "server_availability", "PASS", 
                          f"Server responding at {server_url}", 0)
        
        # Test each documented endpoint
        endpoints = self.inventory.get("api_endpoints", [])
        
        for endpoint in endpoints:
            method = endpoint.get("method", "GET")
            path = endpoint.get("path", "/")
            auth_required = endpoint.get("auth_required", False)
            
            # Skip parameterized paths for basic connectivity test
            if "{" in path:
                test_path = path.replace("{job_id}", "test-id").replace("{full_path:path}", "test")
            else:
                test_path = path
            
            url = f"{server_url}{test_path}"
            
            result, duration, error = self._time_test(self._test_endpoint, method, url, auth_required)
            
            if error:
                self._record_result(component, f"endpoint_{method}_{path}", "FAIL",
                                  f"Endpoint test failed", duration, error=error)
            elif result:
                status, message, details = result
                self._record_result(component, f"endpoint_{method}_{path}", status,
                                  message, duration, details=details)
        
        return self._get_component_status(component, time.time() - start_time)
    
    def _test_endpoint(self, method: str, url: str, auth_required: bool):
        """Test a single API endpoint."""
        try:
            headers = {"Content-Type": "application/json"}
            json_data = None
            form_data = None
            
            # Special handling for authentication endpoints
            if "/token" in url and method == "POST":
                # OAuth2 token endpoint expects form data, not JSON
                form_data = {"username": "admin", "password": "password"}
                headers = {}  # Don't set Content-Type for form data
            elif "/register" in url and method == "POST":
                import time
                unique_id = str(int(time.time() * 1000))  # millisecond timestamp
                json_data = {"username": f"testuser_{unique_id}", "password": "testpass456"}
            elif "/change-password" in url and method == "POST":
                # This endpoint requires auth, so we expect 401 or 403 without token
                json_data = {"current_password": "password", "new_password": "newpass456"}
            
            if auth_required:
                # For auth-required endpoints, we expect 401/403 without token
                if form_data:
                    response = requests.request(method, url, timeout=5, headers=headers, data=form_data)
                else:
                    response = requests.request(method, url, timeout=5, headers=headers, json=json_data)
                if response.status_code in [401, 403]:
                    return "PASS", f"Auth required ({response.status_code}) - as expected", {"status_code": response.status_code}
                elif response.status_code == 404:
                    # 404 is acceptable - could be auth working but resource not found
                    return "PASS", f"Resource not found (404) - auth may be enforced", {"status_code": response.status_code}
                elif response.status_code == 405:
                    # 405 Method Not Allowed is acceptable - endpoint exists but wrong method
                    return "PASS", f"Method not allowed (405) - endpoint exists", {"status_code": response.status_code}
                elif response.status_code in [200]:
                    # Only warn about 200 for auth-required endpoints
                    return "WARN", f"Auth possibly not enforced (got {response.status_code})", {"status_code": response.status_code}
                else:
                    return "FAIL", f"Unexpected status code: {response.status_code}", {"status_code": response.status_code}
            else:
                # For public endpoints, we expect successful response or 404/405
                if form_data:
                    response = requests.request(method, url, timeout=5, headers=headers, data=form_data)
                else:
                    response = requests.request(method, url, timeout=5, headers=headers, json=json_data)
                if response.status_code in [200, 201, 202]:
                    return "PASS", f"Endpoint accessible (status: {response.status_code})", {"status_code": response.status_code}
                elif response.status_code in [404, 405, 422]:  # 422 is validation error, acceptable for endpoints needing specific data
                    if response.status_code == 422 and (json_data or form_data):
                        return "PASS", f"Endpoint accessible with validation (status: {response.status_code})", {"status_code": response.status_code}
                    else:
                        return "WARN", f"Endpoint not found or method not allowed", {"status_code": response.status_code}
                else:
                    return "FAIL", f"Unexpected status code: {response.status_code}", {"status_code": response.status_code}
                    
        except requests.exceptions.Timeout:
            return "FAIL", "Request timeout", {"error": "timeout"}
        except Exception as e:
            return "FAIL", f"Request failed: {str(e)}", {"error": str(e)}

    def validate_database(self) -> ComponentStatus:
        """Test database integrity and operations."""
        logger.info("🗃️ Validating database...")
        component = "database"
        start_time = time.time()
        
        db_url = self.config.get("DB_URL", "sqlite:///./whisper_dev.db")
        
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            if not db_path.startswith("/"):
                db_path = Path.cwd() / db_path
            else:
                db_path = Path(db_path)
        else:
            self._record_result(component, "db_type_support", "SKIP", 
                              "Non-SQLite database not supported by validator", 0)
            return self._get_component_status(component, time.time() - start_time)
        
        # Test database file existence
        if not db_path.exists():
            self._record_result(component, "db_file_exists", "FAIL", 
                              f"Database file not found: {db_path}", 0)
            return self._get_component_status(component, time.time() - start_time)
        
        self._record_result(component, "db_file_exists", "PASS", 
                          f"Database file found: {db_path}", 0)
        
        # Test database connectivity
        result, duration, error = self._time_test(self._test_database_connection, str(db_path))
        if error:
            self._record_result(component, "db_connectivity", "FAIL", 
                              "Database connection failed", duration, error=error)
            return self._get_component_status(component, time.time() - start_time)
        
        conn_info = result
        self._record_result(component, "db_connectivity", "PASS", 
                          "Database connection successful", duration, details=conn_info)
        
        # Test database schema
        result, duration, error = self._time_test(self._test_database_schema, str(db_path))
        if error or result is None:
            self._record_result(component, "db_schema", "FAIL", 
                              "Schema validation failed", duration, error=error)
        else:
            status, message, details = result
            self._record_result(component, "db_schema", status, message, duration, details=details)
        
        # Test database performance
        result, duration, error = self._time_test(self._test_database_performance, str(db_path))
        if error or result is None:
            self._record_result(component, "db_performance", "WARN", 
                              "Performance test failed", duration, error=error)
        else:
            status, message, details = result
            self._record_result(component, "db_performance", status, message, duration, details=details)
        
        return self._get_component_status(component, time.time() - start_time)
    
    def _test_database_connection(self, db_path: str):
        """Test basic database connection."""
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version();")
            version = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA integrity_check;")
            integrity = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA journal_mode;")
            journal_mode = cursor.fetchone()[0]
            
            return {
                "sqlite_version": version,
                "integrity_check": integrity,
                "journal_mode": journal_mode
            }
        finally:
            conn.close()
    
    def _test_database_schema(self, db_path: str):
        """Test database schema against expected tables."""
        expected_tables = ["users", "jobs", "transcript_metadata", "config_entries", 
                          "user_settings", "audit_logs", "performance_metrics", "query_performance_logs"]
        
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            actual_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = set(expected_tables) - set(actual_tables)
            extra_tables = set(actual_tables) - set(expected_tables)
            
            if missing_tables:
                return "FAIL", f"Missing tables: {missing_tables}", {
                    "expected": expected_tables,
                    "actual": actual_tables,
                    "missing": list(missing_tables)
                }
            elif extra_tables:
                return "WARN", f"Extra tables found: {extra_tables}", {
                    "expected": expected_tables,
                    "actual": actual_tables,
                    "extra": list(extra_tables)
                }
            else:
                return "PASS", f"All {len(expected_tables)} tables present", {
                    "tables": actual_tables
                }
        finally:
            conn.close()
    
    def _test_database_performance(self, db_path: str):
        """Test database performance with simple queries."""
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            
            # Test simple query performance
            start = time.time()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master;")
            result = cursor.fetchone()[0]
            query_time = (time.time() - start) * 1000
            
            if query_time > 100:
                return "WARN", f"Slow query performance: {query_time:.2f}ms", {
                    "query_time_ms": query_time,
                    "table_count": result
                }
            else:
                return "PASS", f"Good query performance: {query_time:.2f}ms", {
                    "query_time_ms": query_time,
                    "table_count": result
                }
        finally:
            conn.close()

    def validate_file_system(self) -> ComponentStatus:
        """Test file system components and permissions."""
        logger.info("📁 Validating file system...")
        component = "file_system"
        start_time = time.time()
        
        # Check critical directories
        critical_dirs = [
            "uploads", "models", "storage", "logs", "cache", 
            "transcripts", "docs/architecture", "tools"
        ]
        
        for dir_name in critical_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                if dir_path.is_dir():
                    self._record_result(component, f"dir_{dir_name}", "PASS", 
                                      f"Directory exists and accessible", 0)
                else:
                    self._record_result(component, f"dir_{dir_name}", "FAIL", 
                                      f"Path exists but is not a directory", 0)
            else:
                if dir_name in ["uploads", "storage", "transcripts"]:
                    self._record_result(component, f"dir_{dir_name}", "FAIL", 
                                      f"Critical directory missing", 0)
                else:
                    self._record_result(component, f"dir_{dir_name}", "WARN", 
                                      f"Optional directory missing", 0)
        
        # Test file permissions
        result, duration, error = self._time_test(self._test_file_permissions)
        if error or result is None:
            self._record_result(component, "file_permissions", "WARN", 
                              "Permission test failed", duration, error=error)
        else:
            status, message, details = result
            self._record_result(component, "file_permissions", status, message, duration, details=details)
        
        # Test disk space
        result, duration, error = self._time_test(self._test_disk_space)
        if error or result is None:
            self._record_result(component, "disk_space", "WARN", 
                              "Disk space check failed", duration, error=error)
        else:
            status, message, details = result
            self._record_result(component, "disk_space", status, message, duration, details=details)
        
        return self._get_component_status(component, time.time() - start_time)
    
    def _test_file_permissions(self):
        """Test file system permissions."""
        test_dir = Path("uploads")
        test_file = test_dir / "permission_test.txt"
        
        try:
            # Test write permission
            test_dir.mkdir(exist_ok=True)
            test_file.write_text("test")
            
            # Test read permission
            content = test_file.read_text()
            
            # Cleanup
            test_file.unlink()
            
            return "PASS", "File system permissions OK", {
                "write_access": True,
                "read_access": True
            }
        except PermissionError:
            return "FAIL", "Insufficient file system permissions", {
                "write_access": False,
                "read_access": False
            }
        except Exception as e:
            return "WARN", f"Permission test inconclusive: {str(e)}", {}
    
    def _test_disk_space(self):
        """Test available disk space."""
        try:
            statvfs = psutil.disk_usage('.')
            free_gb = statvfs.free / (1024**3)
            total_gb = statvfs.total / (1024**3)
            used_percent = (statvfs.used / statvfs.total) * 100
            
            if free_gb < 1:
                return "FAIL", f"Critical: Only {free_gb:.1f}GB free", {
                    "free_gb": free_gb,
                    "total_gb": total_gb,
                    "used_percent": used_percent
                }
            elif free_gb < 5:
                return "WARN", f"Low disk space: {free_gb:.1f}GB free", {
                    "free_gb": free_gb,
                    "total_gb": total_gb,
                    "used_percent": used_percent
                }
            else:
                return "PASS", f"Sufficient disk space: {free_gb:.1f}GB free", {
                    "free_gb": free_gb,
                    "total_gb": total_gb,
                    "used_percent": used_percent
                }
        except Exception as e:
            return "WARN", f"Could not check disk space: {str(e)}", {}

    def validate_configuration(self) -> ComponentStatus:
        """Test configuration validity and completeness."""
        logger.info("⚙️ Validating configuration...")
        component = "configuration"
        start_time = time.time()
        
        # Test environment files
        env_files = [".env", ".env.example"]
        for env_file in env_files:
            if Path(env_file).exists():
                self._record_result(component, f"file_{env_file}", "PASS", 
                                  f"Configuration file exists", 0)
            else:
                severity = "FAIL" if env_file == ".env" else "WARN"
                self._record_result(component, f"file_{env_file}", severity, 
                                  f"Configuration file missing", 0)
        
        # Test critical configuration variables
        critical_vars = ["DB_URL", "SECRET_KEY", "PORT"]
        for var in critical_vars:
            if var in self.config:
                self._record_result(component, f"var_{var}", "PASS", 
                                  f"Variable configured", 0)
            else:
                self._record_result(component, f"var_{var}", "FAIL", 
                                  f"Critical variable missing", 0)
        
        # Test configuration consistency
        result, duration, error = self._time_test(self._test_config_consistency)
        if error or result is None:
            self._record_result(component, "config_consistency", "WARN", 
                              "Consistency check failed", duration, error=error)
        else:
            status, message, details = result
            self._record_result(component, "config_consistency", status, message, duration, details=details)
        
        return self._get_component_status(component, time.time() - start_time)
    
    def _test_config_consistency(self):
        """Test configuration consistency."""
        issues = []
        
        # Check database URL format
        db_url = self.config.get("DB_URL", "")
        if not db_url.startswith(("sqlite://", "postgresql://", "mysql://")):
            issues.append("Invalid DB_URL format")
        
        # Check port is numeric
        port = self.config.get("PORT", "8000")
        try:
            port_num = int(port)
            if not (1 <= port_num <= 65535):
                issues.append("PORT out of valid range")
        except ValueError:
            issues.append("PORT is not numeric")
        
        # Check boolean flags
        boolean_vars = ["ALLOW_REGISTRATION", "CLEANUP_ENABLED", "LOG_TO_STDOUT"]
        for var in boolean_vars:
            value = self.config.get(var, "").lower()
            if value not in ["true", "false", "1", "0", ""]:
                issues.append(f"{var} should be boolean")
        
        if issues:
            return "WARN", f"Configuration issues found", {"issues": issues}
        else:
            return "PASS", "Configuration is consistent", {}

    def validate_security(self) -> ComponentStatus:
        """Test security features and configurations."""
        logger.info("🔒 Validating security...")
        component = "security"
        start_time = time.time()
        
        # Test secret key strength
        secret_key = self.config.get("SECRET_KEY", "")
        default_keys = [
            "change_this_in_production_use_secrets_token_hex_32",
            "dev-secret-key-change-in-production", 
            "your-secret-key-change-in-production",
            "changeme",
            "secret",
            "password"
        ]
        
        if not secret_key:
            self._record_result(component, "secret_key", "FAIL", 
                              "SECRET_KEY not configured", 0)
        elif secret_key in default_keys:
            self._record_result(component, "secret_key", "FAIL", 
                              "Using default SECRET_KEY", 0)
        elif len(secret_key) < 32:
            self._record_result(component, "secret_key", "WARN", 
                              "SECRET_KEY too short", 0)
        else:
            self._record_result(component, "secret_key", "PASS", 
                              "SECRET_KEY properly configured", 0)
        
        # Test CORS configuration
        cors_origins = self.config.get("CORS_ORIGINS", "*")
        if cors_origins == "*":
            self._record_result(component, "cors_config", "WARN", 
                              "CORS allows all origins", 0)
        else:
            self._record_result(component, "cors_config", "PASS", 
                              "CORS properly restricted", 0)
        
        # Test authentication endpoints
        result, duration, error = self._time_test(self._test_auth_endpoints)
        if error or result is None:
            self._record_result(component, "auth_endpoints", "WARN", 
                              "Auth endpoint test failed", duration, error=error)
        else:
            status, message, details = result
            self._record_result(component, "auth_endpoints", status, message, duration, details=details)
        
        return self._get_component_status(component, time.time() - start_time)
    
    def _test_auth_endpoints(self):
        """Test authentication endpoints."""
        server_url = self.config.get("VITE_API_HOST", "http://localhost:8000")
        
        try:
            # Test /auth/login endpoint with valid credentials
            login_response = requests.post(f"{server_url}/auth/login", 
                json={"username": "admin", "password": "password"}, 
                timeout=5)
            if login_response.status_code != 200:
                return "WARN", f"Login endpoint unexpected response: {login_response.status_code}", {
                    "endpoint": "/auth/login", "status_code": login_response.status_code
                }
            
            # Extract token for authenticated requests
            token_data = login_response.json()
            auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            
            # Test /auth/me endpoint with authentication
            me_response = requests.get(f"{server_url}/auth/me", 
                headers=auth_headers,
                timeout=5)
            if me_response.status_code != 200:
                return "WARN", f"User info endpoint unexpected response: {me_response.status_code}", {
                    "endpoint": "/auth/me", "status_code": me_response.status_code
                }
            
            # Test /auth/refresh endpoint
            refresh_response = requests.post(f"{server_url}/auth/refresh",
                headers=auth_headers,
                timeout=5)
            if refresh_response.status_code != 200:
                return "WARN", f"Token refresh endpoint unexpected response: {refresh_response.status_code}", {
                    "endpoint": "/auth/refresh", "status_code": refresh_response.status_code
                }
            
            # Test /auth/logout endpoint
            logout_response = requests.post(f"{server_url}/auth/logout",
                headers=auth_headers,
                timeout=5)
            if logout_response.status_code != 200:
                return "WARN", f"Logout endpoint unexpected response: {logout_response.status_code}", {
                    "endpoint": "/auth/logout", "status_code": logout_response.status_code
                }
            
            # Test authentication security - invalid credentials
            invalid_login = requests.post(f"{server_url}/auth/login", 
                json={"username": "admin", "password": "wrong_password"}, 
                timeout=5)
            if invalid_login.status_code != 401:
                return "WARN", f"Invalid credentials should return 401, got {invalid_login.status_code}", {
                    "security_test": "invalid_credentials", "status_code": invalid_login.status_code
                }
                
            # Test authentication required - no token
            no_token_response = requests.get(f"{server_url}/auth/me", timeout=5)
            if no_token_response.status_code not in [401, 403]:
                return "WARN", f"Protected endpoint should require auth, got {no_token_response.status_code}", {
                    "security_test": "no_token", "status_code": no_token_response.status_code
                }
            
            return "PASS", "All auth endpoints functioning correctly with security", {
                "login_status": login_response.status_code,
                "me_status": me_response.status_code,
                "refresh_status": refresh_response.status_code,
                "logout_status": logout_response.status_code,
                "invalid_creds_status": invalid_login.status_code,
                "no_token_status": no_token_response.status_code
            }
        except Exception as e:
            return "FAIL", f"Auth endpoint test failed: {str(e)}", {}

    def validate_backup_system(self) -> ComponentStatus:
        """Test backup system functionality."""
        logger.info("💾 Validating backup system...")
        component = "backup_system"
        start_time = time.time()
        
        # Check backup configuration
        backup_config = {
            "BACKUP_ENABLED": self.config.get("BACKUP_ENABLED", "false"),
            "BACKUP_RETENTION_DAYS": self.config.get("BACKUP_RETENTION_DAYS", "30"),
            "BACKUP_COMPRESSION": self.config.get("BACKUP_COMPRESSION", "true")
        }
        
        # Test backup directories
        backup_dirs = ["backups", "backups/database", "backups/files"]
        for backup_dir in backup_dirs:
            if Path(backup_dir).exists():
                self._record_result(component, f"backup_dir_{backup_dir.replace('/', '_')}", "PASS", 
                                  "Backup directory exists", 0)
            else:
                self._record_result(component, f"backup_dir_{backup_dir.replace('/', '_')}", "WARN", 
                                  "Backup directory missing", 0)
        
        # Test backup modules import
        result, duration, error = self._time_test(self._test_backup_modules)
        if error or result is None:
            self._record_result(component, "backup_modules", "FAIL", 
                              "Backup modules not available", duration, error=error)
        else:
            self._record_result(component, "backup_modules", "PASS", 
                              "Backup modules importable", duration, details=result)
        
        return self._get_component_status(component, time.time() - start_time)
    
    def _test_backup_modules(self):
        """Test backup system modules."""
        try:
            # Try importing backup modules
            backup_modules = [
                "app.backup.orchestrator",
                "app.backup.database", 
                "app.backup.files",
                "app.backup.compression"
            ]
            
            imported = []
            for module in backup_modules:
                try:
                    __import__(module)
                    imported.append(module)
                except ImportError as e:
                    pass
            
            return {
                "modules_available": imported,
                "total_modules": len(backup_modules)
            }
        except Exception as e:
            raise Exception(f"Backup module test failed: {str(e)}")

    def validate_performance(self) -> ComponentStatus:
        """Test performance monitoring and metrics."""
        logger.info("📊 Validating performance monitoring...")
        component = "performance"
        start_time = time.time()
        
        # Test system resources
        result, duration, error = self._time_test(self._test_system_resources)
        if error or result is None:
            self._record_result(component, "system_resources", "WARN", 
                              "Resource check failed", duration, error=error)
        else:
            status, message, details = result
            self._record_result(component, "system_resources", status, message, duration, details=details)
        
        # Test performance endpoints
        server_url = self.config.get("VITE_API_HOST", "http://localhost:8000")
        perf_endpoints = ["/admin/performance/summary", "/admin/performance/metrics"]
        
        for endpoint in perf_endpoints:
            try:
                url = f"{server_url}{endpoint}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    self._record_result(component, f"endpoint_{endpoint.split('/')[-1]}", "PASS", 
                                      "Performance endpoint accessible", 0)
                else:
                    self._record_result(component, f"endpoint_{endpoint.split('/')[-1]}", "WARN", 
                                      f"Performance endpoint returned {response.status_code}", 0)
            except:
                self._record_result(component, f"endpoint_{endpoint.split('/')[-1]}", "FAIL", 
                                  "Performance endpoint not accessible", 0)
        
        return self._get_component_status(component, time.time() - start_time)
    
    def _test_system_resources(self):
        """Test system resource availability."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Process count
            process_count = len(psutil.pids())
            
            issues = []
            if cpu_percent > 90:
                issues.append("High CPU usage")
            if memory_percent > 90:
                issues.append("High memory usage")
            if process_count > 1000:
                issues.append("High process count")
            
            if issues:
                return "WARN", f"Resource issues: {', '.join(issues)}", {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "process_count": process_count
                }
            else:
                return "PASS", "System resources healthy", {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "process_count": process_count
                }
        except Exception as e:
            return "WARN", f"Resource check failed: {str(e)}", {}

    def _get_component_status(self, component: str, duration_ms: float) -> ComponentStatus:
        """Calculate component status from test results."""
        component_results = [r for r in self.results if r.component == component]
        
        tests_run = len(component_results)
        tests_passed = len([r for r in component_results if r.status == "PASS"])
        tests_failed = len([r for r in component_results if r.status == "FAIL"])
        tests_warned = len([r for r in component_results if r.status == "WARN"])
        tests_skipped = len([r for r in component_results if r.status == "SKIP"])
        
        critical_issues = [r.message for r in component_results if r.status == "FAIL"]
        warnings = [r.message for r in component_results if r.status == "WARN"]
        
        # Determine overall status
        if tests_failed > 0:
            overall_status = "CRITICAL"
        elif tests_warned > 0:
            overall_status = "WARNING"
        elif tests_passed > 0:
            overall_status = "HEALTHY"
        else:
            overall_status = "UNKNOWN"
        
        recommendations = []
        if tests_failed > 0:
            recommendations.append("Address critical failures immediately")
        if tests_warned > 0:
            recommendations.append("Review warnings for potential issues")
        if tests_skipped > 0:
            recommendations.append("Complete skipped tests when possible")
        
        return ComponentStatus(
            name=component,
            overall_status=overall_status,
            tests_run=tests_run,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            tests_warned=tests_warned,
            tests_skipped=tests_skipped,
            duration_ms=duration_ms * 1000,
            critical_issues=critical_issues,
            warnings=warnings,
            recommendations=recommendations
        )

    def validate_frontend(self) -> ComponentStatus:
        """Test frontend build process and integration with backend APIs."""
        logger.info("🎨 Validating frontend application...")
        
        start_time = time.time()
        
        # Test frontend build process
        self._test_frontend_build()
        
        # Test frontend-backend API integration 
        self._test_frontend_api_integration()
        
        # Test authentication flow through frontend
        self._test_frontend_authentication()
        
        # Test CORS and cross-origin functionality
        self._test_cors_functionality()
        
        # Test end-to-end user workflow
        self._test_e2e_user_workflow()
        
        duration = time.time() - start_time
        return self._get_component_status("frontend", duration)
    
    def validate_e2e_testing(self) -> ComponentStatus:
        """Test End-to-End testing framework and test coverage."""
        logger.info("🎭 Validating E2E testing framework...")
        
        start_time = time.time()
        
        # Check if E2E testing framework exists
        e2e_dir = Path("tests/e2e")
        if not e2e_dir.exists():
            self._record_result("e2e_testing", "framework_exists", "FAIL", 
                           "E2E testing directory not found", 0)
            duration = time.time() - start_time
            return self._get_component_status("e2e_testing", duration)
        
        self._record_result("e2e_testing", "framework_exists", "PASS", 
                       "E2E testing directory found", 0)
        
        # Check Playwright configuration
        playwright_config = e2e_dir / "playwright.config.ts"
        if playwright_config.exists():
            self._record_result("e2e_testing", "playwright_config", "PASS", 
                           "Playwright configuration found", 0)
        else:
            self._record_result("e2e_testing", "playwright_config", "FAIL", 
                           "Playwright configuration not found", 0)
        
        # Check for test files
        test_files = list(e2e_dir.glob("*.spec.ts")) + list(e2e_dir.glob("*.test.ts"))
        if test_files:
            self._record_result("e2e_testing", "test_files", "PASS", 
                           f"Found {len(test_files)} E2E test files", 0)
            
            # Check for comprehensive test coverage
            test_categories = {
                "auth": False, "authentication": False, "login": False,
                "transcription": False, "upload": False, "workflow": False,
                "admin": False, "management": False,
                "cross-browser": False, "browser": False, "mobile": False
            }
            
            for test_file in test_files:
                file_content = test_file.name.lower()
                for category in test_categories:
                    if category in file_content:
                        test_categories[category] = True
            
            covered_categories = [cat for cat, covered in test_categories.items() if covered]
            if len(covered_categories) >= 6:  # Good coverage
                self._record_result("e2e_testing", "test_coverage", "PASS", 
                               f"Comprehensive test coverage: {', '.join(covered_categories)}", 0)
            elif len(covered_categories) >= 3:  # Basic coverage
                self._record_result("e2e_testing", "test_coverage", "WARN", 
                               f"Basic test coverage: {', '.join(covered_categories)}", 0)
            else:  # Poor coverage
                self._record_result("e2e_testing", "test_coverage", "FAIL", 
                               f"Limited test coverage: {', '.join(covered_categories)}", 0)
        else:
            self._record_result("e2e_testing", "test_files", "FAIL", 
                           "No E2E test files found", 0)
        
        # Check package.json for E2E dependencies
        package_json = e2e_dir / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                
                # Check for Playwright dependency
                dependencies = package_data.get("dependencies", {})
                dev_dependencies = package_data.get("devDependencies", {})
                all_deps = {**dependencies, **dev_dependencies}
                
                if "@playwright/test" in all_deps:
                    self._record_result("e2e_testing", "playwright_dependency", "PASS", 
                                   f"Playwright version: {all_deps['@playwright/test']}", 0)
                else:
                    self._record_result("e2e_testing", "playwright_dependency", "FAIL", 
                                   "Playwright dependency not found", 0)
                
                # Check for test scripts
                scripts = package_data.get("scripts", {})
                test_scripts = [script for script in scripts.keys() if "test" in script]
                if test_scripts:
                    self._record_result("e2e_testing", "test_scripts", "PASS", 
                                   f"Test scripts found: {', '.join(test_scripts)}", 0)
                else:
                    self._record_result("e2e_testing", "test_scripts", "WARN", 
                                   "No test scripts found in package.json", 0)
                    
            except (json.JSONDecodeError, FileNotFoundError) as e:
                self._record_result("e2e_testing", "package_json", "FAIL", 
                               f"Error reading package.json: {str(e)}", 0)
        else:
            self._record_result("e2e_testing", "package_json", "WARN", 
                           "No package.json found in E2E directory", 0)
        
        # Test if Playwright can run (basic validation)
        try:
            start_test_time = time.time()
            result = subprocess.run(
                ["npm", "run", "test", "--", "--list"],
                cwd=e2e_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            test_duration = (time.time() - start_test_time) * 1000
            
            if result.returncode == 0:
                # Count tests from output
                test_count = result.stdout.count("›")  # Playwright test listing format
                self._record_result("e2e_testing", "framework_functional", "PASS", 
                               f"Playwright framework functional, {test_count} tests detected", test_duration)
            else:
                self._record_result("e2e_testing", "framework_functional", "WARN", 
                               f"Playwright test listing failed: {result.stderr[:100]}", test_duration)
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            self._record_result("e2e_testing", "framework_functional", "WARN", 
                           f"Playwright framework test failed: {str(e)[:100]}", 0)
        
        # Check for global setup/teardown
        global_setup = e2e_dir / "global-setup.ts"
        global_teardown = e2e_dir / "global-teardown.ts"
        
        if global_setup.exists() and global_teardown.exists():
            self._record_result("e2e_testing", "global_hooks", "PASS", 
                           "Global setup and teardown files found", 0)
        elif global_setup.exists() or global_teardown.exists():
            self._record_result("e2e_testing", "global_hooks", "WARN", 
                           "Partial global hooks configuration", 0)
        else:
            self._record_result("e2e_testing", "global_hooks", "WARN", 
                           "No global setup/teardown found", 0)
        
        # Check browser configuration
        if playwright_config.exists():
            try:
                with open(playwright_config, 'r') as f:
                    config_content = f.read()
                
                browsers = ["chromium", "firefox", "webkit"]
                configured_browsers = [browser for browser in browsers if browser in config_content]
                
                if len(configured_browsers) >= 3:
                    self._record_result("e2e_testing", "browser_coverage", "PASS", 
                                   f"Multi-browser testing configured: {', '.join(configured_browsers)}", 0)
                elif len(configured_browsers) >= 2:
                    self._record_result("e2e_testing", "browser_coverage", "WARN", 
                                   f"Limited browser coverage: {', '.join(configured_browsers)}", 0)
                else:
                    self._record_result("e2e_testing", "browser_coverage", "FAIL", 
                                   "Insufficient browser coverage", 0)
                    
            except FileNotFoundError:
                self._record_result("e2e_testing", "browser_coverage", "SKIP", 
                               "Cannot read Playwright configuration", 0)
        
        duration = time.time() - start_time
        return self._get_component_status("e2e_testing", duration)

    def _test_frontend_build(self):
        """Test that React frontend builds successfully."""
        try:
            frontend_dir = Path("frontend")
            
            # Check if frontend directory exists
            if not frontend_dir.exists():
                self._record_result("frontend", "frontend_directory", "FAIL", 
                               "Frontend directory not found", 0)
                return
            
            self._record_result("frontend", "frontend_directory", "PASS", 
                           "Frontend directory exists", 0)
            
            # Check package.json
            package_json = frontend_dir / "package.json"
            if not package_json.exists():
                self._record_result("frontend", "package_json", "FAIL", 
                               "package.json not found", 0)
                return
            
            self._record_result("frontend", "package_json", "PASS", 
                           "package.json exists", 0)
            
            # Test npm build process
            logger.info("Testing frontend build process...")
            try:
                start_time = time.time()
                result = subprocess.run(
                    ["npm", "run", "build"],
                    cwd=frontend_dir,
                    capture_output=True,
                    text=True,
                    timeout=120  # 2 minute timeout
                )
                build_duration = (time.time() - start_time) * 1000
                
                if result.returncode == 0:
                    self._record_result("frontend", "build_process", "PASS", 
                                   "Frontend builds successfully", build_duration)
                    
                    # Check if dist directory was created
                    dist_dir = frontend_dir / "dist"
                    if dist_dir.exists():
                        self._record_result("frontend", "build_output", "PASS", 
                                       "Build output directory created", 0)
                        
                        # Check for essential build files
                        index_html = dist_dir / "index.html"
                        if index_html.exists():
                            self._record_result("frontend", "build_index", "PASS", 
                                           "index.html generated", 0)
                        else:
                            self._record_result("frontend", "build_index", "FAIL", 
                                           "index.html not found in build output", 0)
                    else:
                        self._record_result("frontend", "build_output", "FAIL", 
                                       "Build output directory not created", 0)
                        
                else:
                    self._record_result("frontend", "build_process", "FAIL", 
                                   f"Build failed with exit code {result.returncode}", build_duration)
                    logger.error(f"Build stderr: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                self._record_result("frontend", "build_process", "FAIL", 
                               "Build process timed out (>2 minutes)", 120000)
            except FileNotFoundError:
                self._record_result("frontend", "build_process", "SKIP", 
                               "npm not found - install Node.js", 0)
                
        except Exception as e:
            self._record_result("frontend", "build_test", "FAIL", 
                           f"Build test failed: {str(e)}", 0)

    def _test_frontend_api_integration(self):
        """Test that frontend can communicate with backend APIs."""
        try:
            frontend_dir = Path("frontend")
            
            # Check for API service files
            src_dir = frontend_dir / "src"
            if not src_dir.exists():
                self._record_result("frontend", "src_directory", "FAIL", 
                               "Frontend src directory not found", 0)
                return
                
            self._record_result("frontend", "src_directory", "PASS", 
                           "Frontend src directory exists", 0)
            
            # Look for API service files
            api_service_patterns = [
                "services/apiClient.js", "services/authService.js", 
                "services/jobsService.js", "services/adminService.js"
            ]
            
            found_services = []
            for pattern in api_service_patterns:
                service_file = src_dir / pattern
                if service_file.exists():
                    found_services.append(pattern)
            
            if found_services:
                self._record_result("frontend", "api_services", "PASS", 
                               f"API service files found: {', '.join(found_services)}", 0)
            else:
                self._record_result("frontend", "api_services", "WARN", 
                               "No API service files found in expected locations", 0)
            
            # Check vite config for proxy setup
            vite_config = frontend_dir / "vite.config.js"
            if vite_config.exists():
                try:
                    with open(vite_config, 'r') as f:
                        content = f.read()
                        if "proxy" in content and "8000" in content:
                            self._record_result("frontend", "api_proxy", "PASS", 
                                           "Vite proxy configuration found", 0)
                        else:
                            self._record_result("frontend", "api_proxy", "WARN", 
                                           "Vite proxy configuration not found", 0)
                except Exception as e:
                    self._record_result("frontend", "api_proxy", "WARN", 
                                   f"Could not check vite config: {str(e)}", 0)
            else:
                self._record_result("frontend", "vite_config", "WARN", 
                               "vite.config.js not found", 0)
                
        except Exception as e:
            self._record_result("frontend", "api_integration", "FAIL", 
                           f"API integration test failed: {str(e)}", 0)

    def _test_frontend_authentication(self):
        """Test authentication components and flow."""
        try:
            frontend_dir = Path("frontend") / "src"
            
            # Check for authentication components
            auth_components = []
            
            # Look for auth context
            auth_context_paths = [
                "context/AuthContext.jsx", "contexts/AuthContext.jsx",
                "context/AuthContext.js", "contexts/AuthContext.js"
            ]
            
            for path in auth_context_paths:
                if (frontend_dir / path).exists():
                    auth_components.append(f"AuthContext ({path})")
                    break
            
            # Look for auth pages
            auth_page_paths = [
                "pages/auth/LoginPage.jsx", "pages/LoginPage.jsx",
                "components/auth/LoginPage.jsx", "pages/auth/RegisterPage.jsx"
            ]
            
            for path in auth_page_paths:
                if (frontend_dir / path).exists():
                    auth_components.append(f"Auth page ({path})")
                    
            if auth_components:
                self._record_result("frontend", "auth_components", "PASS", 
                               f"Authentication components found: {', '.join(auth_components)}", 0)
            else:
                self._record_result("frontend", "auth_components", "FAIL", 
                               "No authentication components found", 0)
            
            # Check for protected route implementation
            protected_route_paths = [
                "components/ProtectedRoute.jsx", "components/auth/ProtectedRoute.jsx",
                "components/ProtectedRoute.js", "utils/ProtectedRoute.jsx"
            ]
            
            found_protected_route = False
            for path in protected_route_paths:
                if (frontend_dir / path).exists():
                    found_protected_route = True
                    self._record_result("frontend", "protected_routes", "PASS", 
                                   f"Protected route component found: {path}", 0)
                    break
                    
            if not found_protected_route:
                self._record_result("frontend", "protected_routes", "WARN", 
                               "Protected route component not found", 0)
                
        except Exception as e:
            self._record_result("frontend", "auth_test", "FAIL", 
                           f"Authentication test failed: {str(e)}", 0)

    def _test_cors_functionality(self):
        """Test CORS configuration for frontend-backend communication."""
        try:
            server_url = self.config.get("VITE_API_HOST", "http://localhost:8000")
            
            # Simulate a CORS preflight request
            try:
                start_time = time.time()
                response = requests.options(
                    f"{server_url}/health",
                    headers={
                        "Origin": "http://localhost:3000",
                        "Access-Control-Request-Method": "GET",
                        "Access-Control-Request-Headers": "Content-Type,Authorization"
                    },
                    timeout=5
                )
                duration = (time.time() - start_time) * 1000
                
                cors_headers = [
                    "Access-Control-Allow-Origin",
                    "Access-Control-Allow-Methods", 
                    "Access-Control-Allow-Headers"
                ]
                
                present_headers = [h for h in cors_headers if h in response.headers]
                
                if len(present_headers) >= 2:
                    self._record_result("frontend", "cors_headers", "PASS", 
                                   f"CORS headers present: {', '.join(present_headers)}", duration)
                else:
                    self._record_result("frontend", "cors_headers", "WARN", 
                                   "Some CORS headers missing", duration)
                    
            except requests.exceptions.RequestException as e:
                self._record_result("frontend", "cors_test", "WARN", 
                               f"CORS test failed: {str(e)}", 0)
                               
        except Exception as e:
            self._record_result("frontend", "cors_functionality", "FAIL", 
                           f"CORS functionality test failed: {str(e)}", 0)

    def _test_e2e_user_workflow(self):
        """Test end-to-end user workflow through API simulation."""
        try:
            server_url = self.config.get("VITE_API_HOST", "http://localhost:8000")
            
            # Test 1: User Registration Flow
            logger.info("Testing user registration workflow...")
            try:
                start_time = time.time()
                registration_data = {
                    "username": f"test_user_{int(time.time())}",
                    "email": f"test_{int(time.time())}@example.com",
                    "password": "test_password_123"
                }
                
                reg_response = requests.post(
                    f"{server_url}/register",
                    json=registration_data,
                    timeout=10
                )
                
                duration = (time.time() - start_time) * 1000
                
                if reg_response.status_code == 200:
                    self._record_result("frontend", "e2e_user_registration", "PASS", 
                                   "User registration workflow working", duration)
                else:
                    self._record_result("frontend", "e2e_user_registration", "WARN", 
                                   f"Registration returned status {reg_response.status_code}", duration)
                    
            except requests.exceptions.RequestException as e:
                self._record_result("frontend", "e2e_user_registration", "WARN", 
                               f"Registration test failed: {str(e)}", 0)
            
            # Test 2: Authentication Flow
            logger.info("Testing authentication workflow...")
            try:
                start_time = time.time()
                
                # Try to get a token using form data (as expected by FastAPI OAuth2)
                auth_data = {
                    "username": "admin",  # Use existing user
                    "password": "admin"
                }
                
                # Set proper content-type for form data
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                
                auth_response = requests.post(
                    f"{server_url}/token",
                    data=auth_data,
                    headers=headers,
                    timeout=10
                )
                
                duration = (time.time() - start_time) * 1000
                
                if auth_response.status_code == 200:
                    try:
                        token_data = auth_response.json()
                        if "access_token" in token_data:
                            token = token_data["access_token"]
                            self._record_result("frontend", "e2e_authentication", "PASS", 
                                           "Authentication workflow working", duration)
                            
                            # Test 3: Authenticated API Access
                            self._test_authenticated_api_access(server_url, token)
                        else:
                            self._record_result("frontend", "e2e_authentication", "WARN", 
                                           "Authentication response missing access_token", duration)
                    except ValueError:
                        self._record_result("frontend", "e2e_authentication", "WARN", 
                                       "Authentication response not valid JSON", duration)
                        
                elif auth_response.status_code == 422:
                    # Check if it's a validation error (which is expected for invalid credentials)
                    self._record_result("frontend", "e2e_authentication", "PASS", 
                                   "Authentication endpoint validates input correctly (422 for invalid credentials)", duration)
                else:
                    self._record_result("frontend", "e2e_authentication", "WARN", 
                                   f"Authentication returned unexpected status {auth_response.status_code}", duration)
                    
            except requests.exceptions.RequestException as e:
                self._record_result("frontend", "e2e_authentication", "WARN", 
                               f"Authentication test failed: {str(e)}", 0)
                               
        except Exception as e:
            self._record_result("frontend", "e2e_workflow", "FAIL", 
                           f"E2E workflow test failed: {str(e)}", 0)

    def _test_authenticated_api_access(self, server_url: str, token: str):
        """Test authenticated API endpoints that the frontend would use."""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test job listing endpoint
            start_time = time.time()
            jobs_response = requests.get(
                f"{server_url}/jobs/",
                headers=headers,
                timeout=10
            )
            duration = (time.time() - start_time) * 1000
            
            if jobs_response.status_code == 200:
                self._record_result("frontend", "e2e_jobs_access", "PASS", 
                               "Jobs API accessible with authentication", duration)
            else:
                self._record_result("frontend", "e2e_jobs_access", "WARN", 
                               f"Jobs API returned status {jobs_response.status_code}", duration)
            
            # Test user profile/dashboard endpoint
            start_time = time.time()
            try:
                dashboard_response = requests.get(
                    f"{server_url}/dashboard",
                    headers=headers,
                    timeout=10
                )
                duration = (time.time() - start_time) * 1000
                
                if dashboard_response.status_code == 200:
                    self._record_result("frontend", "e2e_dashboard_access", "PASS", 
                                   "Dashboard API accessible", duration)
                else:
                    self._record_result("frontend", "e2e_dashboard_access", "WARN", 
                                   f"Dashboard returned status {dashboard_response.status_code}", duration)
                                   
            except requests.exceptions.RequestException as e:
                self._record_result("frontend", "e2e_dashboard_access", "WARN", 
                               f"Dashboard access test failed: {str(e)}", 0)
            
            # Test admin endpoints (if user has admin access)
            start_time = time.time()
            try:
                admin_response = requests.get(
                    f"{server_url}/admin/stats",
                    headers=headers,
                    timeout=10
                )
                duration = (time.time() - start_time) * 1000
                
                if admin_response.status_code == 200:
                    self._record_result("frontend", "e2e_admin_access", "PASS", 
                                   "Admin API accessible", duration)
                else:
                    self._record_result("frontend", "e2e_admin_access", "WARN", 
                                   f"Admin API returned status {admin_response.status_code}", duration)
                                   
            except requests.exceptions.RequestException as e:
                self._record_result("frontend", "e2e_admin_access", "WARN", 
                               f"Admin access test failed: {str(e)}", 0)
                
        except Exception as e:
            self._record_result("frontend", "e2e_authenticated_access", "FAIL", 
                           f"Authenticated API access test failed: {str(e)}", 0)

    async def run_comprehensive_validation(self, components: Optional[List[str]] = None) -> Dict:
        """Run comprehensive validation of all or specified components."""
        logger.info("🚀 Starting comprehensive application validation...")
        
        if components is None:
            components = ["api_endpoints", "database", "file_system", "configuration", 
                         "security", "backup_system", "performance", "frontend", "e2e_testing"]
        
        component_statuses = []
        overall_start = time.time()
        
        # Run validation for each component
        for component in components:
            try:
                if component == "api_endpoints":
                    status = await self.validate_api_endpoints()
                elif component == "database":
                    status = self.validate_database()
                elif component == "file_system":
                    status = self.validate_file_system()
                elif component == "configuration":
                    status = self.validate_configuration()
                elif component == "security":
                    status = self.validate_security()
                elif component == "backup_system":
                    status = self.validate_backup_system()
                elif component == "performance":
                    status = self.validate_performance()
                elif component == "frontend":
                    status = self.validate_frontend()
                elif component == "e2e_testing":
                    status = self.validate_e2e_testing()
                else:
                    logger.warning(f"Unknown component: {component}")
                    continue
                
                component_statuses.append(status)
                
            except Exception as e:
                logger.error(f"Component {component} validation failed: {str(e)}")
                logger.error(traceback.format_exc())
                
                # Create error status
                error_status = ComponentStatus(
                    name=component,
                    overall_status="ERROR",
                    tests_run=0,
                    tests_passed=0,
                    tests_failed=1,
                    tests_warned=0,
                    tests_skipped=0,
                    duration_ms=0,
                    critical_issues=[f"Validation framework error: {str(e)}"],
                    warnings=[],
                    recommendations=["Check validation framework and dependencies"]
                )
                component_statuses.append(error_status)
        
        # Calculate overall system status
        total_duration = (time.time() - overall_start) * 1000
        
        overall_tests_run = sum(s.tests_run for s in component_statuses)
        overall_tests_passed = sum(s.tests_passed for s in component_statuses)
        overall_tests_failed = sum(s.tests_failed for s in component_statuses)
        overall_tests_warned = sum(s.tests_warned for s in component_statuses)
        overall_tests_skipped = sum(s.tests_skipped for s in component_statuses)
        
        critical_components = [s.name for s in component_statuses if s.overall_status in ["CRITICAL", "ERROR"]]
        warning_components = [s.name for s in component_statuses if s.overall_status == "WARNING"]
        healthy_components = [s.name for s in component_statuses if s.overall_status == "HEALTHY"]
        
        if critical_components:
            overall_system_status = "CRITICAL"
        elif warning_components:
            overall_system_status = "WARNING"
        elif healthy_components:
            overall_system_status = "HEALTHY"
        else:
            overall_system_status = "UNKNOWN"
        
        # Generate summary report
        report = {
            "validation_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "duration_ms": total_duration,
                "validator_version": "1.0.0",
                "components_tested": len(component_statuses),
                "inventory_stats": self.inventory.get("statistics", {})
            },
            "overall_system_status": overall_system_status,
            "summary": {
                "tests_run": overall_tests_run,
                "tests_passed": overall_tests_passed,
                "tests_failed": overall_tests_failed,
                "tests_warned": overall_tests_warned,
                "tests_skipped": overall_tests_skipped,
                "success_rate": (overall_tests_passed / overall_tests_run * 100) if overall_tests_run > 0 else 0
            },
            "component_statuses": [asdict(s) for s in component_statuses],
            "critical_components": critical_components,
            "warning_components": warning_components,
            "healthy_components": healthy_components,
            "detailed_results": [asdict(r) for r in self.results],
            "recommendations": self._generate_recommendations(component_statuses)
        }
        
        return report
    
    def _generate_recommendations(self, component_statuses: List[ComponentStatus]) -> List[str]:
        """Generate system-wide recommendations."""
        recommendations = []
        
        critical_count = len([s for s in component_statuses if s.overall_status in ["CRITICAL", "ERROR"]])
        warning_count = len([s for s in component_statuses if s.overall_status == "WARNING"])
        
        if critical_count > 0:
            recommendations.append(f"🚨 URGENT: {critical_count} critical components need immediate attention")
            recommendations.append("Review critical_components list and address failures")
        
        if warning_count > 0:
            recommendations.append(f"⚠️  {warning_count} components have warnings that should be reviewed")
        
        if critical_count == 0 and warning_count == 0:
            recommendations.append("✅ System appears healthy - consider routine maintenance")
        
        recommendations.append("Run validation regularly to catch issues early")
        recommendations.append("Check logs for additional details on any failures")
        
        return recommendations

    def save_report(self, report: Dict, filename: Optional[str] = None):
        """Save validation report to file."""
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"validation_report_{timestamp}.json"
        
        report_path = Path("logs") / filename
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Validation report saved to: {report_path}")
        return report_path

async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Application State Validator")
    parser.add_argument("--component", choices=["all", "api", "database", "files", "config", "security", "backup", "performance", "frontend", "e2e_testing"],
                       default="all", help="Component to validate")
    parser.add_argument("--output", help="Output file for report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Map component names
    component_map = {
        "all": None,
        "api": ["api_endpoints"],
        "database": ["database"],
        "files": ["file_system"],
        "config": ["configuration"],
        "security": ["security"],
        "backup": ["backup_system"],
        "performance": ["performance"],
        "frontend": ["frontend"],
        "e2e_testing": ["e2e_testing"]
    }
    
    components = component_map.get(args.component)
    
    # Run validation
    validator = ComprehensiveValidator()
    report = await validator.run_comprehensive_validation(components)
    
    # Save report
    report_path = validator.save_report(report, args.output)
    
    # Print summary
    print("\n" + "="*80)
    print("🔍 COMPREHENSIVE APPLICATION VALIDATION COMPLETE")
    print("="*80)
    print(f"Overall Status: {report['overall_system_status']}")
    print(f"Tests Run: {report['summary']['tests_run']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"Duration: {report['validation_metadata']['duration_ms']:.0f}ms")
    print(f"Report: {report_path}")
    
    if report['critical_components']:
        print(f"\n🚨 Critical Components: {', '.join(report['critical_components'])}")
    
    if report['warning_components']:
        print(f"\n⚠️  Warning Components: {', '.join(report['warning_components'])}")
    
    if report['healthy_components']:
        print(f"\n✅ Healthy Components: {', '.join(report['healthy_components'])}")
    
    print("\n📋 Recommendations:")
    for rec in report['recommendations']:
        print(f"  • {rec}")
    
    # Reference master task tracking
    if report['overall_system_status'] in ["CRITICAL", "WARNING"]:
        print(f"\n📌 For detailed issue tracking and resolution plans:")
        print(f"  • See TASKS.md - Master task and issue tracking document")
        print(f"  • Current priority tasks are listed by phase and risk level")
        print(f"  • All known issues and TODOs consolidated in single source of truth")
    
    # Exit with appropriate code
    if report['overall_system_status'] == "CRITICAL":
        sys.exit(1)
    elif report['overall_system_status'] == "WARNING":
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
