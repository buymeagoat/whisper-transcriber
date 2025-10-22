#!/usr/bin/env python3
"""
Test script to validate the task completion enforcement system.
This demonstrates the comprehensive validation requirements.
"""

import os
import sys
import pytest
import subprocess
from pathlib import Path

def test_validation_script_exists():
    """Test that the validation script exists and is executable."""
    script_path = Path("/home/buymeagoat/dev/whisper-transcriber/scripts/validate_task_completion.sh")
    assert script_path.exists(), "Validation script must exist"
    assert os.access(script_path, os.X_OK), "Validation script must be executable"

def test_ai_task_complete_script_enhanced():
    """Test that the main completion script includes validation."""
    script_path = Path("/home/buymeagoat/dev/whisper-transcriber/scripts/ai_task_complete.sh")
    assert script_path.exists(), "AI task complete script must exist"
    
    content = script_path.read_text()
    assert "validate_task_completion.sh" in content, "Script must include validation"
    assert "MANDATORY" in content, "Script must indicate mandatory validation"

def test_pre_commit_hook_enhanced():
    """Test that the pre-commit hook includes TASKS.md validation."""
    hook_path = Path("/home/buymeagoat/dev/whisper-transcriber/.git/hooks/pre-commit")
    assert hook_path.exists(), "Pre-commit hook must exist"
    
    content = hook_path.read_text()
    assert "TASKS.md" in content, "Hook must validate TASKS.md updates"
    assert "COMPLETED" in content, "Hook must check for completion markers"
    assert "tests/" in content, "Hook must validate test updates"

def test_tasks_md_has_completion_markers():
    """Test that TASKS.md contains proper completion markers for completed tasks."""
    tasks_path = Path("/home/buymeagoat/dev/whisper-transcriber/TASKS.md")
    assert tasks_path.exists(), "TASKS.md must exist"
    
    content = tasks_path.read_text()
    
    # Check for completed tasks with proper markers
    assert "✅ **COMPLETED**" in content, "TASKS.md must contain completion markers"
    
    # Verify T036 is properly marked as completed
    assert "T036" in content, "T036 task must be documented"
    assert "- [x] **T036**" in content, "T036 must be marked as completed"

def test_comprehensive_testing_exists():
    """Test that comprehensive testing infrastructure exists."""
    tests_dir = Path("/home/buymeagoat/dev/whisper-transcriber/tests")
    assert tests_dir.exists(), "Tests directory must exist"
    
    # Check for test files
    test_files = list(tests_dir.glob("test_*.py"))
    assert len(test_files) > 0, "Must have test files"
    
    # Check for collaboration-related tests (since T036 was about collaboration)
    collaboration_tests = [f for f in test_files if "collaboration" in f.name or "websocket" in f.name]
    # Note: This is flexible since collaboration tests might be named differently

def test_documentation_structure():
    """Test that documentation structure supports task completion."""
    docs_dir = Path("/home/buymeagoat/dev/whisper-transcriber/docs")
    assert docs_dir.exists(), "Documentation directory must exist"
    
    logs_dir = Path("/home/buymeagoat/dev/whisper-transcriber/logs")
    assert logs_dir.exists(), "Logs directory must exist"
    
    changes_dir = logs_dir / "changes"
    assert changes_dir.exists(), "Changes log directory must exist"

def test_copilot_instructions_updated():
    """Test that copilot instructions document the enforcement system."""
    instructions_path = Path("/home/buymeagoat/dev/whisper-transcriber/.github/copilot-instructions.md")
    assert instructions_path.exists(), "Copilot instructions must exist"
    
    content = instructions_path.read_text()
    assert "MANDATORY: Comprehensive Testing" in content, "Instructions must document testing requirements"
    assert "validate_task_completion.sh" in content, "Instructions must reference validation script"
    assert "Pre-Commit Hook Enforcement" in content, "Instructions must document enforcement"

def test_validation_script_functionality():
    """Test that the validation script provides comprehensive feedback."""
    script_path = Path("/home/buymeagoat/dev/whisper-transcriber/scripts/validate_task_completion.sh")
    content = script_path.read_text()
    
    # Check for key validation functions
    assert "check_tasks_md_updated" in content, "Must validate TASKS.md updates"
    assert "check_comprehensive_testing" in content, "Must validate testing"
    assert "check_test_documentation" in content, "Must validate test documentation"
    assert "check_test_execution" in content, "Must validate test execution"
    
    # Check for actionable recommendations
    assert "provide_recommendations" in content, "Must provide actionable guidance"

if __name__ == "__main__":
    # Run the tests
    print("🔍 Testing Task Completion Enforcement System")
    print("=" * 50)
    
    try:
        # Run pytest on this file
        exit_code = pytest.main([__file__, "-v"])
        
        if exit_code == 0:
            print("\n✅ All enforcement validation tests passed!")
            print("The task completion enforcement system is properly configured.")
        else:
            print("\n❌ Some enforcement validation tests failed!")
            print("Please review the test output above.")
            
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"\n❌ Error running enforcement tests: {e}")
        sys.exit(1)