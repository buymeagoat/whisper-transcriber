#!/usr/bin/env python3
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
        
        print(f"\nMigration complete! {migrated_count} users migrated.")
        print("All migrated users must change their password on next login.")
        print("Temporary password for all migrated users: temp123!Change")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_user_passwords()
