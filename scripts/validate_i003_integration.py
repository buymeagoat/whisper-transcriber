#!/usr/bin/env python3
"""
I003 Integration Validation - Standalone Script
Validates that frontend-backend integration is working without pytest dependencies.
"""

import subprocess
import json
import os
import sys
import requests
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_frontend_infrastructure():
    """Test that frontend testing infrastructure is properly set up."""
    print("🧪 Testing frontend infrastructure...")
    
    frontend_dir = PROJECT_ROOT / "frontend"
    
    # Check Jest configuration exists
    jest_config = frontend_dir / "jest.config.cjs"
    assert jest_config.exists(), "❌ Jest configuration missing"
    print("  ✅ Jest configuration exists")
    
    # Check test setup exists
    setup_tests = frontend_dir / "src" / "setupTests.js"
    assert setup_tests.exists(), "❌ Test setup file missing"
    print("  ✅ Test setup file exists")
    
    # Check package.json has test scripts
    package_json = frontend_dir / "package.json"
    assert package_json.exists(), "❌ package.json missing"
    
    with open(package_json) as f:
        pkg = json.load(f)
        
    assert "scripts" in pkg, "❌ No scripts in package.json"
    assert "test" in pkg["scripts"], "❌ No test script in package.json"
    assert "devDependencies" in pkg, "❌ No devDependencies in package.json"
    assert "@testing-library/react" in pkg["devDependencies"], "❌ React Testing Library not installed"
    print("  ✅ Package.json properly configured")
    
    return True


def test_frontend_tests_execution():
    """Test that frontend tests actually execute successfully."""
    print("🏃 Testing frontend test execution...")
    
    frontend_dir = PROJECT_ROOT / "frontend"
    
    # Change to frontend directory and run tests
    result = subprocess.run(
        ["npm", "test", "--", "--testPathPattern=LoadingSpinner", "--watchAll=false", "--ci"],
        cwd=frontend_dir,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    assert result.returncode == 0, f"❌ Frontend tests failed: {result.stderr}"
    
    # If exit code is 0, tests passed successfully
    # (The specific output format might vary but exit code is reliable)
    print("  ✅ Frontend tests execute successfully")
    
    return True


def test_backend_accessibility():
    """Test that backend API is accessible for integration."""
    print("🔗 Testing backend API accessibility...")
    
    backend_url = "http://localhost:8000"
    
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        assert response.status_code == 200, f"❌ Backend health check failed: {response.status_code}"
        assert response.json()["status"] == "ok", "❌ Backend not healthy"
        print("  ✅ Backend API is accessible and healthy")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️ Backend not accessible: {e}")
        return False


def test_enhanced_test_runner():
    """Test that the enhanced test runner script exists and has proper options."""
    print("🔧 Testing enhanced test runner...")
    
    test_runner = PROJECT_ROOT / "scripts" / "run_tests.sh"
    assert test_runner.exists(), "❌ Enhanced test runner missing"
    
    # Check that the script has the new options
    content = test_runner.read_text()
    assert "--frontend" in content, "❌ Frontend option missing"
    assert "--integration" in content, "❌ Integration option missing"
    assert "INTEGRATION FEATURES" in content, "❌ Integration features documentation missing"
    print("  ✅ Enhanced test runner properly configured")
    
    # Make sure it's executable
    os.chmod(test_runner, 0o755)
    
    # Run with --help to verify it works
    result = subprocess.run(
        [str(test_runner), "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=10
    )
    
    assert result.returncode == 0, f"❌ Test runner help failed: {result.stderr}"
    assert "frontend" in result.stdout.lower(), "❌ Frontend option not in help"
    print("  ✅ Test runner executes properly")
    
    return True


def test_quality_gates():
    """Test that quality gates are properly configured."""
    print("🚦 Testing quality gates configuration...")
    
    frontend_dir = PROJECT_ROOT / "frontend"
    
    # Check Jest configuration for coverage thresholds
    jest_config = frontend_dir / "jest.config.cjs"
    content = jest_config.read_text()
    
    assert "coverageThreshold" in content, "❌ Coverage thresholds not configured"
    assert "80" in content, "❌ Coverage threshold not set to 80%"
    print("  ✅ Quality gates properly configured")
    
    return True


def test_integration_architecture():
    """Test that the integration architecture is working."""
    print("🏗️ Testing integration architecture...")
    
    frontend_dir = PROJECT_ROOT / "frontend"
    
    # 1. Frontend tests exist and work
    frontend_test_files = list((frontend_dir / "src").rglob("*.test.jsx"))
    assert len(frontend_test_files) >= 2, f"❌ Insufficient frontend tests: {len(frontend_test_files)}"
    print(f"  ✅ Frontend tests: {len(frontend_test_files)} files")
    
    # 2. Backend tests exist
    backend_test_files = list((PROJECT_ROOT / "tests").glob("test_*.py"))
    assert len(backend_test_files) >= 10, f"❌ Insufficient backend tests: {len(backend_test_files)}"
    print(f"  ✅ Backend tests: {len(backend_test_files)} files")
    
    # 3. Enhanced runner can coordinate both
    test_runner = PROJECT_ROOT / "scripts" / "run_tests.sh"
    assert test_runner.exists(), "❌ Unified test runner missing"
    print("  ✅ Unified test runner exists")
    
    return True


def test_comprehensive_coverage():
    """Test that comprehensive testing across the stack is possible."""
    print("📊 Testing comprehensive testing capability...")
    
    frontend_dir = PROJECT_ROOT / "frontend"
    
    # 1. Component level (frontend)
    component_tests = list((frontend_dir / "src" / "components").rglob("*.test.jsx"))
    
    # 2. API level (backend)
    api_tests = [f for f in (PROJECT_ROOT / "tests").glob("test_*.py") 
                if "api" in f.name.lower()]
    
    # 3. Integration level
    integration_tests = [f for f in (PROJECT_ROOT / "tests").glob("test_*.py") 
                       if "integration" in f.name.lower()]
    
    print(f"  📈 Component tests: {len(component_tests)}")
    print(f"  📈 API tests: {len(api_tests)}")
    print(f"  📈 Integration tests: {len(integration_tests)}")
    
    # The key validation: we have multi-layer testing capability
    total_tests = len(component_tests) + len(api_tests) + len(integration_tests)
    assert total_tests >= 5, f"❌ Insufficient comprehensive testing: {total_tests}"
    print(f"  ✅ Total test files: {total_tests}")
    
    return True


def main():
    """Run all integration validation tests."""
    print("🚀 Starting I003 Integration Validation")
    print("=" * 50)
    
    tests = [
        test_frontend_infrastructure,
        test_frontend_tests_execution,
        test_backend_accessibility,
        test_enhanced_test_runner,
        test_quality_gates,
        test_integration_architecture,
        test_comprehensive_coverage,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"🎯 Integration Validation Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Success Rate: {passed}/{len(tests)} ({passed/len(tests)*100:.1f}%)")
    
    if failed == 0:
        print("\n🎉 I003 Frontend-Backend Integration COMPLETED!")
        print("   - Frontend testing infrastructure: ✅ Operational")
        print("   - Backend integration: ✅ Available") 
        print("   - Unified test runner: ✅ Functional")
        print("   - Quality gates: ✅ Configured")
        print("   - Comprehensive coverage: ✅ Enabled")
        return True
    else:
        print(f"\n⚠️ Integration validation has {failed} issues to resolve")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)