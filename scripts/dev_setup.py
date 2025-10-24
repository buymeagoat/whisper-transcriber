#!/usr/bin/env python3
"""
Development Database Initialization Script
Streamlined version for the new app/ architecture
"""

import os
import sys
from pathlib import Path
import sqlite3

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def init_database():
    """Initialize SQLite database with tables."""
    try:
        from api.orm_bootstrap import Base, SessionLocal, engine
        from sqlalchemy import text
        
        print("🗄️  Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Test database connection
        with SessionLocal() as db:
            result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
            print(f"✅ Database initialized with tables: {', '.join(tables)}")
            
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def test_app_startup():
    """Test that the application can start."""
    try:
        from api.main import app
        print("✅ Application imports successfully")
        return True
    except Exception as e:
        print(f"❌ Application startup test failed: {e}")
        return False

def main():
    """Main development setup function."""
    print("🚀 Whisper Transcriber Development Setup")
    print("=" * 45)
    
    success = True
    
    # Test application import
    if not test_app_startup():
        success = False
    
    # Initialize database
    if not init_database():
        success = False
    
    if success:
        print("\n🎉 Development environment ready!")
        print("Run: cd app && python main.py")
    else:
        print("\n❌ Setup failed. Check errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
