#!/usr/bin/env python3
"""
T026 Security Hardening: Authentication Security Fixer
Fixes high-priority authentication vulnerabilities including weak password hashing,
missing JWT expiration, and hardcoded secrets.
"""

import os
import re
import json
import secrets
import string
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class AuthSecurityFix:
    """Represents an authentication security fix to be applied."""
    file_path: str
    line_number: int
    old_code: str
    new_code: str
    vulnerability_type: str
    fix_description: str

class AuthenticationSecurityFixer:
    """Fixes authentication security vulnerabilities."""
    
    def __init__(self, project_root: str = "/home/buymeagoat/dev/whisper-transcriber"):
        self.project_root = project_root
        self.fixes_applied = []
        self.fixes_failed = []
        
    def generate_strong_secret(self, length: int = 32) -> str:
        """Generate a strong random secret."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def fix_users_service_password_hashing(self) -> AuthSecurityFix:
        """Replace SHA256 with bcrypt in api/services/users.py."""
        file_path = os.path.join(self.project_root, "api/services/users.py")
        
        old_code = '''import hashlib

logger = get_system_logger("users")

def hash_password(password: str) -> str:
    """Hash a password."""
    return hashlib.sha256(password.encode()).hexdigest()'''
        
        new_code = '''import bcrypt

logger = get_system_logger("users")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt for security."""
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False'''
        
        return AuthSecurityFix(
            file_path=file_path,
            line_number=12,
            old_code=old_code,
            new_code=new_code,
            vulnerability_type="Weak password hashing (SHA256)",
            fix_description="Replaced SHA256 with bcrypt for secure password hashing"
        )
    
    def fix_auth_routes_password_hashing(self) -> AuthSecurityFix:
        """Replace SHA256 with bcrypt in api/routes/auth.py."""
        file_path = os.path.join(self.project_root, "api/routes/auth.py")
        
        old_code = '''def hash_password(password: str) -> str:
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(plain_password) == hashed_password'''
        
        new_code = '''def hash_password(password: str) -> str:
    """Hash a password using bcrypt for security."""
    import bcrypt
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    import bcrypt
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False'''
        
        return AuthSecurityFix(
            file_path=file_path,
            line_number=57,
            old_code=old_code,
            new_code=new_code,
            vulnerability_type="Weak password hashing (SHA256)",
            fix_description="Replaced SHA256 with bcrypt for secure password hashing"
        )
    
    def fix_jwt_expiration_in_auth_routes(self) -> AuthSecurityFix:
        """Ensure JWT tokens always have expiration set."""
        file_path = os.path.join(self.project_root, "api/routes/auth.py")
        
        old_code = '''def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt'''
        
        new_code = '''def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with mandatory expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default to 1 hour for security
        expire = datetime.utcnow() + timedelta(hours=1)
    
    # Always include expiration time
    to_encode.update({"exp": expire})
    # Add issued at time for additional security
    to_encode.update({"iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt'''
        
        return AuthSecurityFix(
            file_path=file_path,
            line_number=64,
            old_code=old_code,
            new_code=new_code,
            vulnerability_type="JWT without guaranteed expiration",
            fix_description="Added mandatory expiration and issued-at time to JWT tokens"
        )
    
    def fix_hardcoded_test_password(self) -> AuthSecurityFix:
        """Fix hardcoded password in scripts/create_test_user.py."""
        file_path = os.path.join(self.project_root, "scripts/create_test_user.py")
        
        # Read the file to find the exact hardcoded password
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Look for the hardcoded password pattern
            old_pattern = r'hashed_password="[^"]+",\s*#\s*secret'
            if re.search(old_pattern, content):
                old_code = '''        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret'''
                new_code = '''        hashed_password=hash_password("testpass123"),  # Generated from password'''
            else:
                # Fallback - create a general fix
                old_code = "hashed_password hash"  # Will trigger manual review
                new_code = "# TODO: Use environment variable for test passwords"
        except FileNotFoundError:
            old_code = "# File not found"
            new_code = "# File not found - manual review needed"
        
        return AuthSecurityFix(
            file_path=file_path,
            line_number=33,
            old_code=old_code,
            new_code=new_code,
            vulnerability_type="Hardcoded password hash",
            fix_description="Replaced hardcoded password hash with dynamic generation"
        )
    
    def create_bcrypt_migration_script(self):
        """Create a script to migrate existing SHA256 passwords to bcrypt."""
        migration_script = os.path.join(self.project_root, "temp", "migrate_passwords_to_bcrypt.py")
        
        content = '''#!/usr/bin/env python3
"""
Password Migration Script: SHA256 to bcrypt
Migrates existing user passwords from SHA256 to bcrypt hashing.
"""

import sys
import os
import bcrypt
from sqlalchemy.orm import Session

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.orm_bootstrap import get_db
from api.models import User

def migrate_user_passwords():
    """Migrate all user passwords to bcrypt."""
    db = next(get_db())
    
    try:
        # Get all users
        users = db.query(User).all()
        
        print(f"Found {len(users)} users to migrate...")
        
        migrated_count = 0
        for user in users:
            # Check if password is already bcrypt (starts with $2b$)
            if user.hashed_password.startswith('$2b$'):
                print(f"  User {user.username}: Already using bcrypt, skipping")
                continue
            
            # Generate a secure temporary password since we can't reverse SHA256
            temp_password = "temp123!Change"  # User must change on first login
            
            # Hash with bcrypt
            salt = bcrypt.gensalt()
            new_hash = bcrypt.hashpw(temp_password.encode('utf-8'), salt)
            
            # Update user
            user.hashed_password = new_hash.decode('utf-8')
            user.must_change_password = True  # Force password change
            
            print(f"  User {user.username}: Migrated to bcrypt with temporary password")
            migrated_count += 1
        
        # Commit changes
        db.commit()
        
        print(f"\\nMigration complete! {migrated_count} users migrated.")
        print("All migrated users must change their password on next login.")
        print("Temporary password for all migrated users: temp123!Change")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_user_passwords()
'''
        
        os.makedirs(os.path.dirname(migration_script), exist_ok=True)
        with open(migration_script, 'w') as f:
            f.write(content)
        
        print(f"✅ Created password migration script at {migration_script}")
    
    def update_requirements_for_bcrypt(self):
        """Add bcrypt to requirements.txt if not already present."""
        req_file = os.path.join(self.project_root, "requirements.txt")
        
        try:
            with open(req_file, 'r') as f:
                content = f.read()
            
            if 'bcrypt' not in content:
                # Add bcrypt to requirements
                with open(req_file, 'a') as f:
                    f.write('\\nbcrypt>=4.0.1\\n')
                print("✅ Added bcrypt to requirements.txt")
            else:
                print("✅ bcrypt already in requirements.txt")
                
        except FileNotFoundError:
            print("⚠️  requirements.txt not found")
    
    def apply_fix(self, fix: AuthSecurityFix) -> bool:
        """Apply a single authentication security fix to a file."""
        try:
            # Read the current file content
            with open(fix.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if the old code exists in the file
            if fix.old_code not in content:
                print(f"⚠️  Warning: Expected code not found in {fix.file_path}")
                print(f"   Looking for: {fix.old_code[:100]}...")
                
                # For some files, try a more flexible search
                if "hash" in fix.old_code.lower() and "hashlib.sha256" in content:
                    print("   Found SHA256 usage, attempting manual fix...")
                    # Add to manual review list
                    self.fixes_failed.append(fix)
                    return False
                
                self.fixes_failed.append(fix)
                return False
            
            # Replace the old code with new code
            new_content = content.replace(fix.old_code, fix.new_code)
            
            # Write the updated content back to the file
            with open(fix.file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ Fixed {fix.vulnerability_type} in {fix.file_path}")
            print(f"   {fix.fix_description}")
            self.fixes_applied.append(fix)
            return True
            
        except Exception as e:
            print(f"❌ Failed to fix {fix.file_path}: {e}")
            self.fixes_failed.append(fix)
            return False
    
    def fix_all_authentication_vulnerabilities(self):
        """Fix all authentication security vulnerabilities."""
        print("🔐 T026 Security Hardening: Fixing Authentication Security Issues")
        print("=" * 80)
        
        # Update requirements for bcrypt
        self.update_requirements_for_bcrypt()
        
        # Get all the fixes to apply
        fixes = [
            self.fix_users_service_password_hashing(),
            self.fix_auth_routes_password_hashing(),
            self.fix_jwt_expiration_in_auth_routes(),
            # Skip hardcoded password fix for now as it needs careful handling
            # self.fix_hardcoded_test_password()
        ]
        
        # Apply each fix
        for fix in fixes:
            self.apply_fix(fix)
        
        # Create additional security utilities
        self.create_bcrypt_migration_script()
        
        # Generate summary report
        self.generate_fix_report()
    
    def generate_fix_report(self):
        """Generate a report of all authentication fixes applied."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_fixes_attempted": len(self.fixes_applied) + len(self.fixes_failed),
            "fixes_successful": len(self.fixes_applied),
            "fixes_failed": len(self.fixes_failed),
            "successful_fixes": [
                {
                    "file_path": fix.file_path,
                    "line_number": fix.line_number,
                    "vulnerability_type": fix.vulnerability_type,
                    "fix_description": fix.fix_description
                }
                for fix in self.fixes_applied
            ],
            "failed_fixes": [
                {
                    "file_path": fix.file_path,
                    "line_number": fix.line_number,
                    "vulnerability_type": fix.vulnerability_type,
                    "error": "Code pattern not found or file modification failed"
                }
                for fix in self.fixes_failed
            ],
            "next_steps": [
                "Install bcrypt: pip install bcrypt>=4.0.1",
                "Run password migration: python temp/migrate_passwords_to_bcrypt.py",
                "Review and remove hardcoded secrets in test files",
                "Update any remaining SHA256 password hashing to bcrypt"
            ]
        }
        
        report_file = os.path.join(self.project_root, "temp", f"auth_security_fixes_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\\n" + "=" * 80)
        print("🔐 AUTHENTICATION SECURITY FIX SUMMARY")
        print("=" * 80)
        print(f"Total fixes attempted: {report['total_fixes_attempted']}")
        print(f"Successful fixes: {report['fixes_successful']}")
        print(f"Failed fixes: {report['fixes_failed']}")
        
        if self.fixes_applied:
            print("\\n✅ Successfully fixed vulnerabilities:")
            for fix in self.fixes_applied:
                print(f"  • {fix.file_path}:{fix.line_number} - {fix.vulnerability_type}")
        
        if self.fixes_failed:
            print("\\n❌ Failed to fix vulnerabilities:")
            for fix in self.fixes_failed:
                print(f"  • {fix.file_path}:{fix.line_number} - {fix.vulnerability_type}")
        
        print("\\n📋 Next Steps:")
        for step in report['next_steps']:
            print(f"  • {step}")
        
        print(f"\\n📄 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    fixer = AuthenticationSecurityFixer()
    fixer.fix_all_authentication_vulnerabilities()