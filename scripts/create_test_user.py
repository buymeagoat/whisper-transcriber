#!/usr/bin/env python3
"""Create a test user for authentication testing."""

import sys
import os
import asyncio
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.models import User
from api.orm_bootstrap import bootstrap_orm

async def create_test_user():
    """Create a test user with known credentials."""
    try:
        # Initialize the ORM
        await bootstrap_orm()
        
        # Check if user already exists
        existing_user = await User.get_or_none(username="testuser@example.com")
        if existing_user:
            print(f"✅ Test user already exists: testuser@example.com")
            print(f"   User ID: {existing_user.id}")
            print(f"   Is Admin: {existing_user.is_admin}")
            return
        
        # Create new test user
        user = await User.create(
            username="testuser@example.com",
            email="testuser@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
            is_admin=False
        )
        
        print(f"✅ Created test user: testuser@example.com")
        print(f"   User ID: {user.id}")
        print(f"   Password: secret")
        print(f"   Is Admin: {user.is_admin}")
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")

if __name__ == "__main__":
    asyncio.run(create_test_user())
