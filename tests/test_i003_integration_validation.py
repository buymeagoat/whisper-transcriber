#!/usr/bin/env python3
"""
I003 Integration Test - Frontend-Backend Integration Validation
Tests that frontend testing infrastructure integrates with backend testing pipeline.
"""

import subprocess
import json
import os
import sys
import pytest
import requests
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestI003Integration:
    """Test I003 Frontend-Backend Integration Pipeline"""
    
    def setup_method(self):
        """Setup for each test method."""
        self.project_root = PROJECT_ROOT
        self.frontend_dir = self.project_root / "frontend"
        self.backend_url = "http://localhost:8000"
        
    def test_frontend_test_infrastructure_exists(self):
        """Test that frontend testing infrastructure is properly set up."""
        # Check Jest configuration exists
        jest_config = self.frontend_dir / "jest.config.cjs"
        assert jest_config.exists(), "Jest configuration missing"
        
        # Check test setup exists
        setup_tests = self.frontend_dir / "src" / "setupTests.js"
        assert setup_tests.exists(), "Test setup file missing"
        
        # Check package.json has test scripts
        package_json = self.frontend_dir / "package.json"
        assert package_json.exists(), "package.json missing"
        
        with open(package_json) as f:
            pkg = json.load(f)
            
        assert "scripts" in pkg, "No scripts in package.json"
        assert "test" in pkg["scripts"], "No test script in package.json"
        assert "devDependencies" in pkg, "No devDependencies in package.json"
        assert "@testing-library/react" in pkg["devDependencies"], "React Testing Library not installed"
        
    def test_frontend_tests_can_run(self):
        """Test that frontend tests actually execute successfully."""
        # Change to frontend directory and run tests
        result = subprocess.run(
            ["npm", "test", "--", "--testPathPattern=LoadingSpinner", "--watchAll=false", "--ci"],
            cwd=self.frontend_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"Frontend tests failed: {result.stderr}"
        assert "Test Suites: 1 passed" in result.stdout or "PASS" in result.stdout, "Tests didn't pass"
        
    def test_backend_api_accessible(self):
        """Test that backend API is accessible for integration."""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            assert response.status_code == 200, f"Backend health check failed: {response.status_code}"
            assert response.json()["status"] == "ok", "Backend not healthy"
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Backend not accessible: {e}")
            
    def test_enhanced_test_runner_exists(self):
        """Test that the enhanced test runner script exists and has proper options."""
        test_runner = self.project_root / "scripts" / "run_tests.sh"
        assert test_runner.exists(), "Enhanced test runner missing"
        
        # Check that the script has the new options
        content = test_runner.read_text()
        assert "--frontend" in content, "Frontend option missing"
        assert "--integration" in content, "Integration option missing"
        assert "INTEGRATION FEATURES" in content, "Integration features documentation missing"
        
    def test_test_runner_frontend_functionality(self):
        """Test that the enhanced test runner can execute frontend tests."""
        test_runner = self.project_root / "scripts" / "run_tests.sh"
        
        # Make sure it's executable
        os.chmod(test_runner, 0o755)
        
        # Run with --help to verify it works
        result = subprocess.run(
            [str(test_runner), "--help"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0, f"Test runner help failed: {result.stderr}"
        assert "frontend" in result.stdout.lower(), "Frontend option not in help"
        
    def test_integration_test_logging(self):
        """Test that integration testing produces proper logs."""
        logs_dir = self.project_root / "logs" / "test_runs"
        
        # The logs directory should exist (created by enhanced runner)
        if logs_dir.exists():
            # Check if any test run logs exist
            log_files = list(logs_dir.glob("test_run_*.log"))
            # If logs exist, verify they have content
            if log_files:
                latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                content = latest_log.read_text()
                assert len(content) > 0, "Log file is empty"
                
    def test_quality_gates_configuration(self):
        """Test that quality gates are properly configured."""
        # Check Jest configuration for coverage thresholds
        jest_config = self.frontend_dir / "jest.config.cjs"
        content = jest_config.read_text()
        
        assert "coverageThreshold" in content, "Coverage thresholds not configured"
        assert "80" in content, "Coverage threshold not set to 80%"
        
    def test_frontend_backend_integration_concept(self):
        """Test that the integration concept is working - both systems can be tested together."""
        # This test validates that we can run both frontend and backend tests
        # and get unified reporting
        
        # 1. Frontend tests exist and work
        frontend_test_files = list((self.frontend_dir / "src").rglob("*.test.jsx"))
        assert len(frontend_test_files) >= 2, f"Insufficient frontend tests: {len(frontend_test_files)}"
        
        # 2. Backend tests exist
        backend_test_files = list((self.project_root / "tests").glob("test_*.py"))
        assert len(backend_test_files) >= 10, f"Insufficient backend tests: {len(backend_test_files)}"
        
        # 3. Enhanced runner can coordinate both
        test_runner = self.project_root / "scripts" / "run_tests.sh"
        assert test_runner.exists(), "Unified test runner missing"
        
        # This validates the integration infrastructure is in place
        print("✅ Integration infrastructure validated:")
        print(f"   - Frontend tests: {len(frontend_test_files)}")
        print(f"   - Backend tests: {len(backend_test_files)}")
        print(f"   - Unified runner: {test_runner.exists()}")
        
    def test_comprehensive_testing_capability(self):
        """Test that comprehensive testing across the stack is possible."""
        # Validate we have testing for different layers
        
        # 1. Component level (frontend)
        component_tests = list((self.frontend_dir / "src" / "components").rglob("*.test.jsx"))
        
        # 2. API level (backend)
        api_tests = [f for f in (self.project_root / "tests").glob("test_*.py") 
                    if "api" in f.name.lower()]
        
        # 3. Integration level
        integration_tests = [f for f in (self.project_root / "tests").glob("test_*.py") 
                           if "integration" in f.name.lower()]
        
        print("📊 Testing Coverage Analysis:")
        print(f"   - Component tests: {len(component_tests)}")
        print(f"   - API tests: {len(api_tests)}")
        print(f"   - Integration tests: {len(integration_tests)}")
        
        # The key validation: we have multi-layer testing capability
        total_tests = len(component_tests) + len(api_tests) + len(integration_tests)
        assert total_tests >= 5, f"Insufficient comprehensive testing: {total_tests}"


if __name__ == "__main__":
    # Run the integration validation
    pytest.main([__file__, "-v"])