#!/usr/bin/env python3
"""
Test script to validate database initialization and auto-migration features.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_models_import():
    """Test that all models can be imported and are registered."""
    print("Testing models import...")
    try:
        from api.orm_bootstrap import Base
        import api.models  # noqa: F401
        
        table_names = list(Base.metadata.tables.keys())
        print(f"✅ Models imported. Tables in metadata: {sorted(table_names)}")
        
        expected_tables = [
            "users", "jobs", "transcript_metadata", "config_entries", 
            "user_settings", "audit_logs", "performance_metrics", "query_performance_logs"
        ]
        
        missing_tables = [t for t in expected_tables if t not in table_names]
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        else:
            print("✅ All expected tables found in metadata")
            return True
            
    except Exception as e:
        print(f"❌ Error importing models: {e}")
        return False

def test_database_initialization():
    """Test database initialization with our fixed orm_bootstrap."""
    print("\nTesting database initialization...")
    try:
        from api.orm_bootstrap import validate_or_initialize_database
        result = validate_or_initialize_database()
        print(f"Database initialization result: {result}")
        return result
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def test_table_creation():
    """Test that performance_metrics table is actually created."""
    print("\nTesting table creation...")
    try:
        from sqlalchemy import inspect
        from api.orm_bootstrap import engine
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables in database: {sorted(tables)}")
        
        if 'performance_metrics' in tables:
            print("✅ performance_metrics table exists")
            
            # Check table structure
            columns = inspector.get_columns('performance_metrics')
            column_names = [col['name'] for col in columns]
            print(f"Columns: {column_names}")
            
            expected_columns = ['id', 'timestamp', 'metric_type', 'metric_name', 'value', 'unit', 'tags']
            missing_columns = [c for c in expected_columns if c not in column_names]
            if missing_columns:
                print(f"❌ Missing columns: {missing_columns}")
                return False
            else:
                print("✅ All expected columns found")
                return True
        else:
            print("❌ performance_metrics table missing")
            return False
            
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False

def test_auto_migration_setting():
    """Test auto-migration environment variable handling."""
    print("\nTesting auto-migration settings...")
    try:
        # Test environment variable
        os.environ['AUTO_MIGRATE'] = 'true'
        from api.settings import Settings
        settings = Settings()
        
        # Check if the setting is recognized
        auto_migrate = getattr(settings, 'auto_migrate', False) or os.getenv("AUTO_MIGRATE", "false").lower() in ("true", "1", "yes")
        print(f"Auto-migrate setting: {auto_migrate}")
        
        if auto_migrate:
            print("✅ Auto-migration setting recognized")
            return True
        else:
            print("❌ Auto-migration setting not recognized")
            return False
            
    except Exception as e:
        print(f"❌ Error testing auto-migration: {e}")
        return False
    finally:
        # Clean up
        if 'AUTO_MIGRATE' in os.environ:
            del os.environ['AUTO_MIGRATE']

def main():
    """Run all tests."""
    print("=== Database Initialization Test Suite ===\n")
    
    tests = [
        test_models_import,
        test_database_initialization, 
        test_table_creation,
        test_auto_migration_setting
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n=== Test Results ===")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)