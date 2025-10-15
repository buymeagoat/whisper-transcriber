#!/usr/bin/env python3
"""
Simple validation script for pagination functionality (Issue #009).

This script tests the basic functionality of the pagination system
without requiring the full test environment setup.
"""

import sys
import os
import traceback
from datetime import datetime, timedelta

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_pagination_imports():
    """Test that all pagination modules can be imported."""
    try:
        from app.pagination import (
            PaginationRequest, JobQueryFilters, CursorGenerator,
            PaginationConfig, PaginationMetadata
        )
        print("✅ All pagination modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Pagination import failed: {e}")
        traceback.print_exc()
        return False

def test_pagination_request_validation():
    """Test PaginationRequest validation."""
    try:
        from app.pagination import PaginationRequest
        
        # Valid request
        valid_request = PaginationRequest(
            page_size=20,
            sort_by="created_at",
            sort_order="desc"
        )
        print("✅ PaginationRequest validation works")
        
        # Test invalid page size
        try:
            invalid_request = PaginationRequest(page_size=200)
            print("❌ Should have rejected large page size")
            return False
        except:
            print("✅ Large page size validation works")
        
        # Test invalid sort field
        try:
            invalid_request = PaginationRequest(sort_by="invalid_field")
            print("❌ Should have rejected invalid sort field")
            return False
        except:
            print("✅ Invalid sort field validation works")
        
        return True
    except Exception as e:
        print(f"❌ PaginationRequest validation failed: {e}")
        traceback.print_exc()
        return False

def test_cursor_generation():
    """Test cursor generation and parsing."""
    try:
        from app.pagination import CursorGenerator
        
        # Generate cursor
        cursor = CursorGenerator.generate_cursor(
            item_id="test-123",
            sort_field_value="2025-10-15T10:00:00",
            sort_by="created_at",
            sort_order="desc"
        )
        
        print(f"✅ Cursor generated: {cursor[:50]}...")
        
        # Parse cursor
        parsed = CursorGenerator.parse_cursor(cursor)
        
        assert parsed["id"] == "test-123"
        assert parsed["sort_value"] == "2025-10-15T10:00:00"
        assert parsed["sort_by"] == "created_at"
        assert parsed["sort_order"] == "desc"
        
        print("✅ Cursor parsing works correctly")
        
        # Test invalid cursor
        try:
            CursorGenerator.parse_cursor("invalid_cursor")
            print("❌ Should have rejected invalid cursor")
            return False
        except:
            print("✅ Invalid cursor rejection works")
        
        return True
    except Exception as e:
        print(f"❌ Cursor generation/parsing failed: {e}")
        traceback.print_exc()
        return False

def test_job_query_filters():
    """Test JobQueryFilters validation."""
    try:
        from app.pagination import JobQueryFilters
        
        # Valid filters
        filters = JobQueryFilters(
            status="completed",
            model_used="small",
            min_file_size=1000,
            max_duration=300
        )
        print("✅ JobQueryFilters validation works")
        
        # Test invalid status
        try:
            invalid_filters = JobQueryFilters(status="invalid_status")
            print("❌ Should have rejected invalid status")
            return False
        except:
            print("✅ Invalid status validation works")
        
        return True
    except Exception as e:
        print(f"❌ JobQueryFilters validation failed: {e}")
        traceback.print_exc()
        return False

def test_schemas_integration():
    """Test integration with response schemas."""
    try:
        from app.schemas import PaginatedJobsResponseSchema, JobResponseSchema
        
        # Create sample data
        sample_job = {
            "id": "test-123",
            "filename": "test.mp3",
            "status": "completed",
            "model_used": "small",
            "created_at": datetime.utcnow(),
            "completed_at": datetime.utcnow(),
            "file_size": 1000,
            "duration": 300,
            "error_message": None
        }
        
        job_response = JobResponseSchema(**sample_job)
        print("✅ JobResponseSchema works")
        
        sample_pagination = {
            "data": [job_response],
            "pagination": {
                "page_size": 20,
                "total_count": 100,
                "has_next": True,
                "has_previous": False,
                "next_cursor": "test_cursor",
                "previous_cursor": None,
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        }
        
        paginated_response = PaginatedJobsResponseSchema(**sample_pagination)
        print("✅ PaginatedJobsResponseSchema works")
        
        return True
    except Exception as e:
        print(f"❌ Schema integration failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all validation tests."""
    print("🔍 Testing Pagination Implementation (Issue #009)")
    print("=" * 50)
    
    tests = [
        ("Pagination Imports", test_pagination_imports),
        ("PaginationRequest Validation", test_pagination_request_validation),
        ("Cursor Generation/Parsing", test_cursor_generation),
        ("JobQueryFilters Validation", test_job_query_filters),
        ("Schema Integration", test_schemas_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All pagination tests passed!")
        return 0
    else:
        print("⚠️  Some pagination tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
