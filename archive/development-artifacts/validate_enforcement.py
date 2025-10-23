#!/usr/bin/env python3
"""
Simple validation script for the task completion enforcement system.
"""

import os
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and report result."""
    path = Path(file_path)
    if path.exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path}")
        return False

def check_file_contains(file_path, content, description):
    """Check if a file contains specific content."""
    path = Path(file_path)
    if not path.exists():
        print(f"❌ {description}: File {file_path} does not exist")
        return False
    
    try:
        file_content = path.read_text()
        if content in file_content:
            print(f"✅ {description}: Found '{content}'")
            return True
        else:
            print(f"❌ {description}: '{content}' not found")
            return False
    except Exception as e:
        print(f"❌ {description}: Error reading file - {e}")
        return False

def main():
    print("🔍 Task Completion Enforcement System Validation")
    print("=" * 55)
    print()
    
    all_checks_passed = True
    
    # Core script files
    print("1. Core Scripts:")
    all_checks_passed &= check_file_exists(
        "/home/buymeagoat/dev/whisper-transcriber/scripts/validate_task_completion.sh",
        "Validation script exists"
    )
    all_checks_passed &= check_file_exists(
        "/home/buymeagoat/dev/whisper-transcriber/scripts/ai_task_complete.sh",
        "Main completion script exists"
    )
    
    # Check script executability
    val_script = Path("/home/buymeagoat/dev/whisper-transcriber/scripts/validate_task_completion.sh")
    main_script = Path("/home/buymeagoat/dev/whisper-transcriber/scripts/ai_task_complete.sh")
    
    if val_script.exists() and os.access(val_script, os.X_OK):
        print("✅ Validation script is executable")
    else:
        print("❌ Validation script is not executable")
        all_checks_passed = False
        
    if main_script.exists() and os.access(main_script, os.X_OK):
        print("✅ Main completion script is executable")
    else:
        print("❌ Main completion script is not executable")
        all_checks_passed = False
    
    print()
    
    # Script content validation
    print("2. Script Content Validation:")
    all_checks_passed &= check_file_contains(
        "/home/buymeagoat/dev/whisper-transcriber/scripts/ai_task_complete.sh",
        "validate_task_completion.sh",
        "Main script includes validation"
    )
    all_checks_passed &= check_file_contains(
        "/home/buymeagoat/dev/whisper-transcriber/scripts/ai_task_complete.sh",
        "MANDATORY",
        "Main script indicates mandatory validation"
    )
    all_checks_passed &= check_file_contains(
        "/home/buymeagoat/dev/whisper-transcriber/scripts/validate_task_completion.sh",
        "check_tasks_md_updated",
        "Validation script checks TASKS.md"
    )
    all_checks_passed &= check_file_contains(
        "/home/buymeagoat/dev/whisper-transcriber/scripts/validate_task_completion.sh",
        "check_comprehensive_testing",
        "Validation script checks testing"
    )
    
    print()
    
    # Pre-commit hook
    print("3. Pre-Commit Hook:")
    all_checks_passed &= check_file_exists(
        "/home/buymeagoat/dev/whisper-transcriber/.git/hooks/pre-commit",
        "Pre-commit hook exists"
    )
    all_checks_passed &= check_file_contains(
        "/home/buymeagoat/dev/whisper-transcriber/.git/hooks/pre-commit",
        "TASKS.md",
        "Pre-commit hook validates TASKS.md"
    )
    all_checks_passed &= check_file_contains(
        "/home/buymeagoat/dev/whisper-transcriber/.git/hooks/pre-commit",
        "✅ **COMPLETED**",
        "Pre-commit hook checks completion markers"
    )
    
    print()
    
    # Documentation
    print("4. Documentation:")
    all_checks_passed &= check_file_exists(
        "/home/buymeagoat/dev/whisper-transcriber/TASKS.md",
        "TASKS.md exists"
    )
    all_checks_passed &= check_file_contains(
        "/home/buymeagoat/dev/whisper-transcriber/TASKS.md",
        "✅ **COMPLETED**",
        "TASKS.md has completion markers"
    )
    all_checks_passed &= check_file_contains(
        "/home/buymeagoat/dev/whisper-transcriber/.github/copilot-instructions.md",
        "MANDATORY: Comprehensive Testing",
        "Copilot instructions document testing requirements"
    )
    all_checks_passed &= check_file_contains(
        "/home/buymeagoat/dev/whisper-transcriber/.github/copilot-instructions.md",
        "validate_task_completion.sh",
        "Copilot instructions reference validation script"
    )
    
    print()
    
    # Directory structure
    print("5. Directory Structure:")
    all_checks_passed &= check_file_exists(
        "/home/buymeagoat/dev/whisper-transcriber/tests",
        "Tests directory exists"
    )
    all_checks_passed &= check_file_exists(
        "/home/buymeagoat/dev/whisper-transcriber/logs",
        "Logs directory exists"
    )
    all_checks_passed &= check_file_exists(
        "/home/buymeagoat/dev/whisper-transcriber/temp",
        "Temp directory exists"
    )
    
    print()
    print("=" * 55)
    
    if all_checks_passed:
        print("🎉 ALL VALIDATION CHECKS PASSED!")
        print("✅ Task completion enforcement system is properly configured.")
        print()
        print("Key Features Implemented:")
        print("- Pre-task validation script with comprehensive checks")
        print("- Enhanced ai_task_complete.sh with mandatory validation")
        print("- Pre-commit hook with TASKS.md and test validation")
        print("- Updated copilot instructions with enforcement documentation")
        print("- Proper directory structure for organized development")
        print()
        print("Usage:")
        print("- ./scripts/validate_task_completion.sh (validate requirements)")
        print("- ./scripts/ai_task_complete.sh (complete task with validation)")
        return True
    else:
        print("❌ SOME VALIDATION CHECKS FAILED!")
        print("Please review the failed checks above and fix any issues.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)