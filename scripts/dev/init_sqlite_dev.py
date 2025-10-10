#!/usr/bin/env python3
"""
SQLite Database Initialization for Development

Creates tables and default admin user for development testing.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def init_sqlite_dev_db():
    """Initialize SQLite database for development"""
    
    print("🗄️  Initializing SQLite development database...")
    
    from api.models import Base
    from api.orm_bootstrap import engine, SessionLocal
    from api.services.users import create_user, get_user_by_username
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    # Create admin user if it doesn't exist
    try:
        admin_user = get_user_by_username('admin')
        if admin_user:
            print(f"✅ Admin user already exists: {admin_user.username}")
        else:
            admin_user = create_user('admin', 'changeme', 'admin')
            print(f"✅ Created admin user: {admin_user.username}")
        
        # Test authentication
        from api.services.users import verify_password
        if verify_password('changeme', admin_user.hashed_password):
            print("✅ Password verification working")
        else:
            print("❌ Password verification failed")
            
        # Create a test user
        test_user = get_user_by_username('testuser')
        if not test_user:
            test_user = create_user('testuser', 'testpass', 'user')
            print(f"✅ Created test user: {test_user.username}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        return False

def test_authentication():
    """Test authentication with the created users"""
    
    print("\n🔐 Testing authentication...")
    
    # Test login endpoint
    import requests
    try:
        response = requests.post(
            "http://localhost:8000/token",
            data={"username": "admin", "password": "changeme"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                print("✅ Login successful - token obtained")
                return data["access_token"]
            else:
                print("❌ Login response missing token")
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Server not running - cannot test login endpoint")
        print("   Run the server first: python scripts/server_entry.py")
    except Exception as e:
        print(f"❌ Login test error: {e}")
    
    return None

def main():
    """Main function"""
    
    print("🧪 SQLite Development Database Setup")
    print("=" * 50)
    
    # Initialize database
    success = init_sqlite_dev_db()
    
    if success:
        print("\n✅ Database initialization complete!")
        print("\nDefault credentials:")
        print("  Admin: admin / changeme")
        print("  Test user: testuser / testpass")
        
        # Test authentication if server is running
        token = test_authentication()
        
        if token:
            print(f"\n🎉 Authentication fully working!")
            print("You can now run the comprehensive tests:")
            print("  python comprehensive_integration_test.py")
        else:
            print("\n⚠️  Start the server to test authentication:")
            print("  python scripts/server_entry.py")
            
    else:
        print("\n❌ Database initialization failed")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
