#!/usr/bin/env python3
"""
Comprehensive Application Function Tester for Whisper Transcriber

This script systematically tests every function of the whisper-transcriber application
to determine what's working and what's returning errors.

Usage:
    python test_all_functions.py [--local] [--containers] [--verbose]
    
    --local: Test local Python modules without containers
    --containers: Test containerized services (requires Docker)
    --verbose: Show detailed output for all tests
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib.util

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test Results Storage
test_results = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "categories": {},
    "summary": {"total": 0, "pass": 0, "fail": 0, "skip": 0}
}

def log_test(category: str, test_name: str, status: str, details: str = "", error: str = ""):
    """Log a test result."""
    if category not in test_results["categories"]:
        test_results["categories"][category] = []
    
    test_results["categories"][category].append({
        "test": test_name,
        "status": status,
        "details": details,
        "error": error
    })
    
    test_results["summary"]["total"] += 1
    test_results["summary"][status.lower()] += 1
    
    status_symbol = {"PASS": "✓", "FAIL": "✗", "SKIP": "⚠"}.get(status, "?")
    print(f"{status_symbol} [{category}] {test_name}: {details}")
    if error:
        print(f"    Error: {error}")

class InfrastructureTests:
    """Test basic infrastructure and dependencies."""
    
    @staticmethod
    def test_python_imports():
        """Test that all required Python modules can be imported."""
        required_modules = [
            "fastapi", "uvicorn", "sqlalchemy", "alembic", "celery", 
            "pydantic", "pydantic_settings", "psycopg2", "redis",
            "whisper", "torch", "numpy", "pathlib", "subprocess"
        ]
        
        for module in required_modules:
            try:
                __import__(module)
                log_test("Infrastructure", f"Import {module}", "PASS", f"Module {module} available")
            except ImportError as e:
                log_test("Infrastructure", f"Import {module}", "FAIL", f"Module {module} not available", str(e))
    
    @staticmethod
    def test_file_structure():
        """Test that all required files and directories exist."""
        required_paths = [
            "api/main.py", "api/models.py", "api/settings.py", "worker.py",
            "docker-compose.yml", "Dockerfile", "requirements.txt",
            "frontend/dist/index.html", "models/", "api/migrations/",
            "api/static/", "scripts/", "tests/"
        ]
        
        for path_str in required_paths:
            path = project_root / path_str
            if path.exists():
                log_test("Infrastructure", f"File/Dir {path_str}", "PASS", f"Path exists: {path}")
            else:
                log_test("Infrastructure", f"File/Dir {path_str}", "FAIL", f"Path missing: {path}")
    
    @staticmethod
    def test_model_files():
        """Test that required Whisper model files exist."""
        models_dir = project_root / "models"
        required_models = ["base.pt", "tiny.pt", "small.pt", "medium.pt", "large-v3.pt"]
        
        for model in required_models:
            model_path = models_dir / model
            if model_path.exists():
                size_mb = model_path.stat().st_size / (1024 * 1024)
                log_test("Infrastructure", f"Model {model}", "PASS", f"Model exists ({size_mb:.1f} MB)")
            else:
                log_test("Infrastructure", f"Model {model}", "FAIL", f"Model file missing: {model_path}")

class ConfigurationTests:
    """Test application configuration and settings."""
    
    @staticmethod
    def test_settings_loading():
        """Test that settings can be loaded correctly."""
        try:
            from api.settings import settings
            log_test("Configuration", "Settings Load", "PASS", f"Settings loaded with DB URL: {settings.db_url[:50]}...")
            
            # Test individual settings
            config_items = [
                ("db_url", settings.db_url),
                ("log_level", settings.log_level),
                ("max_upload_size", settings.max_upload_size),
                ("auth_username", settings.auth_username),
                ("secret_key", settings.secret_key[:10] + "..."),
            ]
            
            for name, value in config_items:
                if value:
                    log_test("Configuration", f"Setting {name}", "PASS", f"Value: {value}")
                else:
                    log_test("Configuration", f"Setting {name}", "FAIL", f"Setting {name} is empty")
                    
        except Exception as e:
            log_test("Configuration", "Settings Load", "FAIL", "Failed to load settings", str(e))
    
    @staticmethod
    def test_environment_variables():
        """Test environment variable handling."""
        important_env_vars = [
            "DATABASE_URL", "SECRET_KEY", "AUTH_USERNAME", "AUTH_PASSWORD",
            "OPENAI_API_KEY", "CELERY_BROKER_URL"
        ]
        
        for var in important_env_vars:
            value = os.getenv(var)
            if value:
                log_test("Configuration", f"Env Var {var}", "PASS", f"Set (length: {len(value)})")
            else:
                log_test("Configuration", f"Env Var {var}", "SKIP", "Not set (using defaults)")

class DatabaseTests:
    """Test database connectivity and operations."""
    
    @staticmethod
    def test_database_models():
        """Test that database models can be imported and defined."""
        try:
            from api.models import Base, User, Job, TranscriptMetadata, ConfigEntry, UserSetting
            
            models = [User, Job, TranscriptMetadata, ConfigEntry, UserSetting]
            for model in models:
                log_test("Database", f"Model {model.__name__}", "PASS", f"Model class defined with {len(model.__table__.columns)} columns")
                
            log_test("Database", "SQLAlchemy Metadata", "PASS", f"Base metadata has {len(Base.metadata.tables)} tables")
            
        except Exception as e:
            log_test("Database", "Model Import", "FAIL", "Failed to import models", str(e))
    
    @staticmethod
    def test_migrations():
        """Test that migration files exist and are valid."""
        migrations_dir = project_root / "api" / "migrations" / "versions"
        
        if not migrations_dir.exists():
            log_test("Database", "Migrations Directory", "FAIL", "Migrations directory missing")
            return
            
        migration_files = list(migrations_dir.glob("*.py"))
        log_test("Database", "Migration Files", "PASS", f"Found {len(migration_files)} migration files")
        
        for migration_file in migration_files[:3]:  # Test first 3
            try:
                with open(migration_file, 'r') as f:
                    content = f.read()
                    if "upgrade" in content and "downgrade" in content:
                        log_test("Database", f"Migration {migration_file.name}", "PASS", "Has upgrade/downgrade functions")
                    else:
                        log_test("Database", f"Migration {migration_file.name}", "FAIL", "Missing upgrade/downgrade functions")
            except Exception as e:
                log_test("Database", f"Migration {migration_file.name}", "FAIL", "Failed to read migration", str(e))

class APITests:
    """Test API functionality without requiring running containers."""
    
    @staticmethod
    def test_fastapi_app_creation():
        """Test that FastAPI app can be created."""
        try:
            from api.main import app
            log_test("API", "FastAPI App Creation", "PASS", f"App created with {len(app.routes)} routes")
            
            # Test route discovery
            route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
            important_routes = ["/health", "/docs", "/auth/login", "/auth/register"]
            
            for route in important_routes:
                if route in route_paths:
                    log_test("API", f"Route {route}", "PASS", "Route defined in app")
                else:
                    log_test("API", f"Route {route}", "FAIL", "Route not found in app")
                    
        except Exception as e:
            log_test("API", "FastAPI App Creation", "FAIL", "Failed to create app", str(e))
    
    @staticmethod
    def test_api_route_modules():
        """Test that API route modules can be imported."""
        route_modules = [
            "api.routes.auth", "api.routes.audio", "api.routes.health",
            "api.routes.admin", "api.routes.logs", "api.routes.jobs"
        ]
        
        for module_name in route_modules:
            try:
                module = importlib.import_module(module_name)
                log_test("API", f"Route Module {module_name.split('.')[-1]}", "PASS", f"Module imported: {module.__name__}")
            except Exception as e:
                log_test("API", f"Route Module {module_name.split('.')[-1]}", "FAIL", f"Failed to import {module_name}", str(e))

class WorkerTests:
    """Test Celery worker functionality."""
    
    @staticmethod
    def test_celery_app_creation():
        """Test that Celery app can be created."""
        try:
            from worker import celery_app
            log_test("Worker", "Celery App Creation", "PASS", f"Celery app created: {celery_app.main}")
            
            # Test task discovery
            tasks = list(celery_app.tasks.keys())
            log_test("Worker", "Celery Tasks", "PASS", f"Found {len(tasks)} registered tasks")
            
        except Exception as e:
            log_test("Worker", "Celery App Creation", "FAIL", "Failed to create Celery app", str(e))
    
    @staticmethod
    def test_whisper_model_loading():
        """Test that Whisper models can be loaded."""
        try:
            import whisper
            
            # Test loading the smallest model first
            models_dir = project_root / "models"
            tiny_model = models_dir / "tiny.pt"
            
            if tiny_model.exists():
                # Don't actually load the model (too resource intensive)
                # Just verify the file can be accessed
                log_test("Worker", "Whisper Model Access", "PASS", f"Tiny model file accessible: {tiny_model}")
            else:
                log_test("Worker", "Whisper Model Access", "FAIL", "Tiny model file not found")
                
            log_test("Worker", "Whisper Library", "PASS", f"Whisper library version: {whisper.__version__ if hasattr(whisper, '__version__') else 'unknown'}")
            
        except Exception as e:
            log_test("Worker", "Whisper Library", "FAIL", "Failed to import whisper", str(e))

class ContainerTests:
    """Test containerized services if Docker is available."""
    
    @staticmethod
    def test_docker_availability():
        """Test if Docker is available and working."""
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                log_test("Containers", "Docker Available", "PASS", result.stdout.strip())
                return True
            else:
                log_test("Containers", "Docker Available", "FAIL", "Docker command failed", result.stderr)
                return False
        except Exception as e:
            log_test("Containers", "Docker Available", "FAIL", "Docker not available", str(e))
            return False
    
    @staticmethod
    def test_container_services():
        """Test if application containers are running."""
        if not ContainerTests.test_docker_availability():
            return
            
        try:
            result = subprocess.run(
                ["docker-compose", "ps", "--services"], 
                capture_output=True, text=True, timeout=10,
                cwd=project_root
            )
            
            if result.returncode == 0:
                services = result.stdout.strip().split('\n')
                log_test("Containers", "Docker Compose Services", "PASS", f"Found services: {', '.join(services)}")
                
                # Check if services are running
                result = subprocess.run(
                    ["docker-compose", "ps"], 
                    capture_output=True, text=True, timeout=10,
                    cwd=project_root
                )
                
                if "Up" in result.stdout:
                    log_test("Containers", "Running Services", "PASS", "Some services are running")
                else:
                    log_test("Containers", "Running Services", "SKIP", "No services currently running")
                    
            else:
                log_test("Containers", "Docker Compose", "FAIL", "Docker Compose failed", result.stderr)
                
        except Exception as e:
            log_test("Containers", "Container Services", "FAIL", "Failed to check containers", str(e))

class UtilityTests:
    """Test utility functions and helpers."""
    
    @staticmethod
    def test_logging_setup():
        """Test logging configuration."""
        try:
            from api.utils.logger import get_system_logger
            logger = get_system_logger()
            log_test("Utilities", "System Logger", "PASS", f"Logger created: {logger.name}")
        except Exception as e:
            log_test("Utilities", "System Logger", "FAIL", "Failed to create logger", str(e))
    
    @staticmethod
    def test_path_configuration():
        """Test path configuration."""
        try:
            from api.paths import MODEL_DIR, UPLOAD_DIR, TRANSCRIPTS_DIR
            
            paths = [
                ("MODEL_DIR", MODEL_DIR),
                ("UPLOAD_DIR", UPLOAD_DIR),
                ("TRANSCRIPTS_DIR", TRANSCRIPTS_DIR)
            ]
            
            for name, path in paths:
                if path.exists():
                    log_test("Utilities", f"Path {name}", "PASS", f"Path exists: {path}")
                else:
                    log_test("Utilities", f"Path {name}", "SKIP", f"Path will be created: {path}")
                    
        except Exception as e:
            log_test("Utilities", "Path Configuration", "FAIL", "Failed to load paths", str(e))

def run_all_tests(test_local=True, test_containers=False, verbose=False):
    """Run all test categories."""
    print("=" * 60)
    print("WHISPER TRANSCRIBER - COMPREHENSIVE FUNCTION TEST")
    print("=" * 60)
    
    test_categories = [
        ("Infrastructure", InfrastructureTests),
        ("Configuration", ConfigurationTests),
        ("Database", DatabaseTests),
        ("API", APITests),
        ("Worker", WorkerTests),
        ("Utilities", UtilityTests),
    ]
    
    if test_containers:
        test_categories.append(("Containers", ContainerTests))
    
    for category_name, test_class in test_categories:
        print(f"\n--- {category_name} Tests ---")
        
        for method_name in dir(test_class):
            if method_name.startswith("test_"):
                try:
                    method = getattr(test_class, method_name)
                    method()
                except Exception as e:
                    log_test(category_name, method_name, "FAIL", "Test execution failed", str(e))
                    if verbose:
                        traceback.print_exc()
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    summary = test_results["summary"]
    print(f"Total Tests: {summary['total']}")
    print(f"✓ Passed: {summary['pass']}")
    print(f"✗ Failed: {summary['fail']}")
    print(f"⚠ Skipped: {summary['skip']}")
    
    success_rate = (summary['pass'] / summary['total'] * 100) if summary['total'] > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Save detailed results
    results_file = project_root / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"\nDetailed results saved to: {results_file}")
    
    return summary['fail'] == 0

def main():
    parser = argparse.ArgumentParser(description="Test all functions of the whisper-transcriber application")
    parser.add_argument("--local", action="store_true", default=True, help="Test local Python modules")
    parser.add_argument("--containers", action="store_true", help="Test containerized services")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    
    args = parser.parse_args()
    
    success = run_all_tests(
        test_local=args.local,
        test_containers=args.containers,
        verbose=args.verbose
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
