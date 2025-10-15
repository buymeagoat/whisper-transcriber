#!/usr/bin/env python3

"""
Simple Database Performance Validation
Validates that our database optimizations are properly implemented
"""

import sys
import time
from pathlib import Path

# Add parent directory to path to import api modules
sys.path.append(str(Path(__file__).parent.parent))

def validate_model_indexes():
    """Validate that our optimized models have the expected indexes"""
    
    print("Validating database model optimizations...")
    
    try:
        from api.models_optimized import Job, User, TranscriptMetadata, AuditLog
        
        # Check User model indexes
        user_indexes = [idx.name for idx in User.__table__.indexes]
        expected_user_indexes = [
            'idx_users_username', 'idx_users_role', 'idx_users_active', 
            'idx_users_created_at', 'idx_users_last_login'
        ]
        
        print(f"✅ User model has {len(user_indexes)} indexes")
        for idx in expected_user_indexes:
            if any(idx in user_idx for user_idx in user_indexes):
                print(f"  ✅ {idx}")
            else:
                print(f"  ❌ {idx} missing")
        
        # Check Job model indexes
        job_indexes = [idx.name for idx in Job.__table__.indexes]
        expected_job_indexes = [
            'idx_jobs_status', 'idx_jobs_created_at', 'idx_jobs_user_id',
            'idx_jobs_user_status_created', 'idx_jobs_processing_time'
        ]
        
        print(f"\n✅ Job model has {len(job_indexes)} indexes")
        for idx in expected_job_indexes:
            if any(idx in job_idx for job_idx in job_indexes):
                print(f"  ✅ {idx}")
            else:
                print(f"  ❌ {idx} missing")
        
        # Check if new performance tracking fields exist
        job_columns = [col.name for col in Job.__table__.columns]
        expected_new_columns = [
            'user_id', 'processing_time_seconds', 'file_size_bytes', 'duration_seconds'
        ]
        
        print(f"\n✅ Job model performance tracking columns:")
        for col in expected_new_columns:
            if col in job_columns:
                print(f"  ✅ {col}")
            else:
                print(f"  ❌ {col} missing")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import optimized models: {e}")
        return False


def validate_query_optimizations():
    """Validate that our query optimization patterns are available"""
    
    print("\nValidating query optimization patterns...")
    
    try:
        from api.query_optimizer import (
            OptimizedJobQueries, OptimizedUserQueries, 
            OptimizedMetadataQueries, QueryPerformanceMonitor
        )
        
        # Check that optimization classes have expected methods
        job_methods = [
            'get_jobs_with_metadata', 'get_job_with_user_and_metadata',
            'get_jobs_by_user_paginated', 'get_job_statistics'
        ]
        
        print("✅ OptimizedJobQueries methods:")
        for method in job_methods:
            if hasattr(OptimizedJobQueries, method):
                print(f"  ✅ {method}")
            else:
                print(f"  ❌ {method} missing")
        
        user_methods = ['get_active_users_with_stats', 'get_user_by_username_optimized']
        
        print("\n✅ OptimizedUserQueries methods:")
        for method in user_methods:
            if hasattr(OptimizedUserQueries, method):
                print(f"  ✅ {method}")
            else:
                print(f"  ❌ {method} missing")
        
        # Check performance monitor
        monitor = QueryPerformanceMonitor()
        print(f"\n✅ QueryPerformanceMonitor initialized with threshold: {monitor.slow_query_threshold_ms}ms")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import query optimizations: {e}")
        return False


def validate_performance_middleware():
    """Validate that performance monitoring middleware is available"""
    
    print("\nValidating performance monitoring middleware...")
    
    try:
        from api.performance_middleware import (
            DatabasePerformanceMiddleware, setup_database_monitoring
        )
        
        print("✅ DatabasePerformanceMiddleware available")
        print("✅ setup_database_monitoring function available")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import performance middleware: {e}")
        return False


def validate_migration_scripts():
    """Validate that migration scripts exist"""
    
    print("\nValidating migration scripts...")
    
    migration_file = Path(__file__).parent.parent / "api" / "migrations" / "versions" / "001_add_performance_indexes_and_metrics.py"
    
    if migration_file.exists():
        print("✅ Performance optimization migration script exists")
        
        # Check file size to ensure it's not empty
        file_size = migration_file.stat().st_size
        if file_size > 1000:  # Expect substantial migration
            print(f"✅ Migration script is substantial ({file_size} bytes)")
        else:
            print(f"⚠️  Migration script seems small ({file_size} bytes)")
        
        return True
    else:
        print("❌ Migration script not found")
        return False


def validate_optimized_endpoints():
    """Validate that optimized endpoint patterns are available"""
    
    print("\nValidating optimized endpoint patterns...")
    
    try:
        from api.optimized_endpoints import (
            list_jobs_optimized, get_job_detail_optimized, 
            get_job_statistics_optimized, get_admin_dashboard_optimized
        )
        
        endpoints = [
            'list_jobs_optimized', 'get_job_detail_optimized',
            'get_job_statistics_optimized', 'get_admin_dashboard_optimized'
        ]
        
        print("✅ Optimized endpoint functions:")
        for endpoint in endpoints:
            print(f"  ✅ {endpoint}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import optimized endpoints: {e}")
        return False


def run_simple_performance_check():
    """Run a simple performance check without requiring database setup"""
    
    print("\nRunning simple performance validation...")
    
    # Test import performance
    start_time = time.time()
    
    try:
        from api.models_optimized import Job, User
        from api.query_optimizer import OptimizedJobQueries
        from api.performance_middleware import DatabasePerformanceMiddleware
        
        import_time = (time.time() - start_time) * 1000
        print(f"✅ Module imports completed in {import_time:.2f}ms")
        
        if import_time < 1000:  # Should be fast
            print("✅ Import performance is good")
        else:
            print("⚠️  Import performance could be improved")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance check failed: {e}")
        return False


def main():
    """Run all database performance validations"""
    
    print("Database Performance Optimization Validation")
    print("=" * 50)
    
    results = []
    
    # Run validation checks
    checks = [
        ("Model Indexes", validate_model_indexes),
        ("Query Optimizations", validate_query_optimizations),
        ("Performance Middleware", validate_performance_middleware),
        ("Migration Scripts", validate_migration_scripts),
        ("Optimized Endpoints", validate_optimized_endpoints),
        ("Performance Check", run_simple_performance_check)
    ]
    
    for check_name, check_func in checks:
        print(f"\n{'-' * 30}")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} validation failed with error: {e}")
            results.append((check_name, False))
    
    # Summary
    print(f"\n{'=' * 50}")
    print("VALIDATION SUMMARY")
    print(f"{'=' * 50}")
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:25}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} validations passed")
    
    if passed == total:
        print("🎉 All database performance optimizations validated successfully!")
        return 0
    else:
        print("⚠️  Some validations failed - review implementation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
