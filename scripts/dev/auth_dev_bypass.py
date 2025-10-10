#!/usr/bin/env python3
"""
Development Authentication Bypass

This script temporarily disables authentication for development/testing.
Can be easily reverted when ready for production.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_auth_bypass():
    """Create a temporary authentication bypass"""
    
    bypass_code = '''
# DEVELOPMENT BYPASS - REMOVE FOR PRODUCTION
from api.models import User

def get_current_user_bypass() -> User:
    """Development bypass - returns a mock admin user"""
    return User(
        id=1,
        username="dev_admin",
        role="admin",
        password_hash="bypass"
    )

def require_admin_bypass() -> User:
    """Development bypass - returns a mock admin user"""
    return get_current_user_bypass()

# Override the real functions
get_current_user = get_current_user_bypass
require_admin = require_admin_bypass
'''
    
    # Create bypass file
    with open("api/auth_bypass.py", "w") as f:
        f.write(bypass_code)
    
    print("✅ Authentication bypass created: api/auth_bypass.py")
    print("   This allows full access for development/testing")
    print("   Remove this file when ready for production")

def apply_auth_bypass():
    """Apply the authentication bypass to the application"""
    
    # Read current auth.py
    with open("api/routes/auth.py", "r") as f:
        content = f.read()
    
    # Check if already bypassed
    if "# AUTH BYPASS ACTIVE" in content:
        print("✅ Authentication bypass already active")
        return
    
    # Add bypass import at the top
    bypass_import = """
# AUTH BYPASS ACTIVE - REMOVE FOR PRODUCTION
from api.auth_bypass import get_current_user_bypass, require_admin_bypass
"""
    
    # Insert after existing imports
    lines = content.split('\n')
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            insert_pos = i + 1
    
    lines.insert(insert_pos, bypass_import)
    
    # Override the functions
    override_code = """
# Override auth functions for development
get_current_user = get_current_user_bypass  
require_admin = require_admin_bypass
"""
    
    # Find the end of the file and add override
    lines.append(override_code)
    
    # Write back
    with open("api/routes/auth.py", "w") as f:
        f.write('\n'.join(lines))
    
    print("✅ Authentication bypass applied to api/routes/auth.py")

def remove_auth_bypass():
    """Remove the authentication bypass"""
    
    # Remove bypass file
    bypass_file = Path("api/auth_bypass.py")
    if bypass_file.exists():
        bypass_file.unlink()
        print("✅ Removed api/auth_bypass.py")
    
    # Read current auth.py
    with open("api/routes/auth.py", "r") as f:
        content = f.read()
    
    # Remove bypass code
    lines = content.split('\n')
    clean_lines = []
    skip_section = False
    
    for line in lines:
        if "# AUTH BYPASS ACTIVE" in line:
            skip_section = True
            continue
        elif skip_section and (line.startswith('#') or line.strip() == ''):
            continue
        elif skip_section and not line.startswith(' ') and line.strip():
            skip_section = False
        
        if not skip_section:
            if "get_current_user = get_current_user_bypass" not in line and \
               "require_admin = require_admin_bypass" not in line:
                clean_lines.append(line)
    
    # Write back clean version
    with open("api/routes/auth.py", "w") as f:
        f.write('\n'.join(clean_lines))
    
    print("✅ Authentication bypass removed from api/routes/auth.py")

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "enable":
            create_auth_bypass()
            apply_auth_bypass()
            print("\n🚀 Authentication bypass enabled for development")
            print("   All endpoints now accessible without authentication")
            print("   Run 'python auth_dev_bypass.py disable' to restore auth")
        elif command == "disable":
            remove_auth_bypass()
            print("\n🔒 Authentication bypass disabled")
            print("   Normal authentication restored")
        else:
            print("Usage: python auth_dev_bypass.py [enable|disable]")
    else:
        print("🔧 Authentication Development Bypass Tool")
        print("=========================================")
        print("Usage:")
        print("  python auth_dev_bypass.py enable   - Disable auth for development")
        print("  python auth_dev_bypass.py disable  - Restore normal authentication")
        print("\nThis tool allows you to temporarily bypass authentication")
        print("for development and testing purposes.")

if __name__ == "__main__":
    main()
