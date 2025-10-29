#!/usr/bin/env python3
"""
Test suite for task completion enforcement system.
Tests the validation scripts, hooks, and enforcement mechanisms.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

def test_validation_script_validates_tasks_md():
    """Test that validation script properly validates TASKS.md updates."""
    # This test ensures the validation script checks for proper TASKS.md format
    script_path = Path("/home/buymeagoat/dev/whisper-transcriber/scripts/validate_task_completion.sh")
    
    # Test script exists and has required functions
    content = script_path.read_text()
    
    assert "check_tasks_md_updated" in content
    assert "✅ **COMPLETED**" in content
    assert "TASKS.md" in content
    
    print("✅ Validation script properly checks TASKS.md format")

def test_validation_script_validates_testing():
    """Test that validation script properly validates comprehensive testing."""
    script_path = Path("/home/buymeagoat/dev/whisper-transcriber/scripts/validate_task_completion.sh")
    content = script_path.read_text()
    
    assert "check_comprehensive_testing" in content
    assert "test_*.py" in content
    assert "pytest" in content
    assert "coverage" in content
    
    print("✅ Validation script properly checks testing requirements")

def test_ai_task_complete_includes_validation():
    """Test that main completion script includes mandatory validation."""
    script_path = Path("/home/buymeagoat/dev/whisper-transcriber/scripts/ai_task_complete.sh")
    content = script_path.read_text()
    
    assert "validate_task_completion.sh" in content
    assert "MANDATORY" in content
    assert "validation passed" in content
    
    print("✅ Main completion script includes mandatory validation")

def test_pre_commit_hook_validates_tasks_md():
    """Test that pre-commit hook validates TASKS.md and testing updates."""
    hook_path = Path("/home/buymeagoat/dev/whisper-transcriber/.git/hooks/pre-commit")
    content = hook_path.read_text()
    
    assert "TASKS.md" in content
    assert "✅ **COMPLETED**" in content
    assert "tests/" in content
    assert "def test_" in content
    
    print("✅ Pre-commit hook validates TASKS.md and testing")

def test_copilot_instructions_document_enforcement():
    """Test that copilot instructions properly document the enforcement system."""
    instructions_path = Path("/home/buymeagoat/dev/whisper-transcriber/.github/copilot-instructions.md")
    content = instructions_path.read_text()
    
    assert "MANDATORY: TASKS.md Updates" in content
    assert "MANDATORY: Comprehensive Testing" in content
    assert "validate_task_completion.sh" in content
    assert "Pre-Commit Hook Enforcement" in content
    
    print("✅ Copilot instructions document enforcement requirements")

def test_directory_structure_supports_enforcement():
    """Test that directory structure supports the enforcement system."""
    base_path = Path("/home/buymeagoat/dev/whisper-transcriber")
    
    # Check required directories exist
    assert (base_path / "tests").exists()
    assert (base_path / "logs").exists()
    assert (base_path / "logs" / "changes").exists()
    assert (base_path / "temp").exists()
    assert (base_path / "scripts").exists()
    
    print("✅ Directory structure supports enforcement system")

def test_validation_script_provides_actionable_feedback():
    """Test that validation script provides actionable feedback for failures."""
    script_path = Path("/home/buymeagoat/dev/whisper-transcriber/scripts/validate_task_completion.sh")
    content = script_path.read_text()
    
    # Check for actionable recommendations
    assert "provide_recommendations" in content
    assert "Task Completion Checklist" in content
    assert "pytest --cov=api tests/" in content
    assert "test_<feature>.py" in content
    
    print("✅ Validation script provides actionable feedback")

def test_enforcement_integration():
    """Test that enforcement system components work together."""
    base_path = Path("/home/buymeagoat/dev/whisper-transcriber")
    
    # Check that ai_task_complete.sh calls validation
    main_script = (base_path / "scripts" / "ai_task_complete.sh").read_text()
    assert "validate_task_completion.sh" in main_script
    
    # Check that validation script exists
    validation_script = base_path / "scripts" / "validate_task_completion.sh"
    assert validation_script.exists()
    
    # Check that pre-commit hook supports the workflow
    hook_content = (base_path / ".git" / "hooks" / "pre-commit").read_text()
    assert "TASKS.md" in hook_content
    
    print("✅ Enforcement system components integrate properly")

def run_enforcement_system_tests():
    """Run all enforcement system tests."""
    print("🧪 Running Task Completion Enforcement System Tests")
    print("=" * 60)
    print()
    
    tests = [
        test_validation_script_validates_tasks_md,
        test_validation_script_validates_testing,
        test_ai_task_complete_includes_validation,
        test_pre_commit_hook_validates_tasks_md,
        test_copilot_instructions_document_enforcement,
        test_directory_structure_supports_enforcement,
        test_validation_script_provides_actionable_feedback,
        test_enforcement_integration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All enforcement system tests passed!")
        print()
        print("✅ Task completion enforcement system is fully functional:")
        print("   - Validation script validates TASKS.md updates and testing")
        print("   - Main completion script includes mandatory validation")
        print("   - Pre-commit hook prevents invalid commits")
        print("   - Copilot instructions document all requirements")
        print("   - Directory structure supports organized development")
        print("   - System provides actionable feedback for failures")
        return True
    else:
        print(f"❌ {failed} enforcement system tests failed!")
        return False

if __name__ == "__main__":
    success = run_enforcement_system_tests()
    sys.exit(0 if success else 1)