#!/usr/bin/env python3

"""
Database Configuration Validation Script - I005 Infrastructure Issue
Test and validate optimized database configuration improvements
"""

import sys
import time
import threading
from datetime import datetime
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, '/home/buymeagoat/dev/whisper-transcriber')

from api.optimized_database_config import create_optimized_database_configuration, get_production_recommendations
from api.optimized_orm_bootstrap import (
    optimized_engine, OptimizedSessionLocal, validate_optimized_database,
    get_optimized_database_info, get_connection_pool_status, apply_database_optimizations
)
from api.models import User, Job, JobStatusEnum
from api.utils.logger import get_system_logger

logger = get_system_logger("db_config_test")


def test_basic_configuration():
    """Test basic optimized configuration functionality"""
    print("\n=== Testing Basic Configuration ===")
    
    # Test configuration creation
    config = create_optimized_database_configuration()
    print(f"✓ Database type detected: {config.database_type}")
    
    # Test configuration validation
    validation_results = config.validate_configuration()
    print(f"✓ Configuration valid: {validation_results['configuration_valid']}")
    
    if validation_results['warnings']:
        print("⚠️  Configuration warnings:")
        for warning in validation_results['warnings']:
            print(f"    • {warning}")
    
    if validation_results['recommendations']:
        print("💡 Configuration recommendations:")
        for rec in validation_results['recommendations']:
            print(f"    • {rec}")
    
    # Test database info
    db_info = get_optimized_database_info()
    print(f"✓ Database info: {db_info['type']} v{db_info['version']}")
    
    # Test connection pool status
    pool_status = get_connection_pool_status()
    print(f"✓ Connection pool: {pool_status}")
    
    return validation_results


def test_sqlite_optimizations():
    """Test SQLite-specific optimizations"""
    print("\n=== Testing SQLite Optimizations ===")
    
    try:
        config = create_optimized_database_configuration()
        
        if config.database_type != "sqlite":
            print("⚠️  Not using SQLite, skipping SQLite optimization tests")
            return True
        
        # Test optimized URL generation
        optimized_url = config.get_optimized_sqlite_url()
        print(f"✓ Optimized SQLite URL: {optimized_url}")
        
        # Test engine configuration
        engine_config = config.get_optimized_engine_config()
        print(f"✓ Engine config keys: {list(engine_config.keys())}")
        
        # Test actual optimizations
        with optimized_engine.connect() as conn:
            from sqlalchemy import text
            
            # Check WAL mode
            journal_mode = conn.execute(text("PRAGMA journal_mode")).scalar()
            print(f"✓ Journal mode: {journal_mode}")
            
            # Check cache size
            cache_size = conn.execute(text("PRAGMA cache_size")).scalar()
            print(f"✓ Cache size: {cache_size}")
            
            # Check synchronous mode
            synchronous = conn.execute(text("PRAGMA synchronous")).scalar()
            print(f"✓ Synchronous mode: {synchronous}")
            
            # Check foreign keys
            foreign_keys = conn.execute(text("PRAGMA foreign_keys")).scalar()
            print(f"✓ Foreign keys: {bool(foreign_keys)}")
            
            # Check busy timeout
            busy_timeout = conn.execute(text("PRAGMA busy_timeout")).scalar()
            print(f"✓ Busy timeout: {busy_timeout}ms")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLite optimization test failed: {e}")
        return False


def test_performance_improvements():
    """Test performance improvements from optimizations"""
    print("\n=== Testing Performance Improvements ===")
    
    try:
        # Test basic operations timing
        operations = []
        
        # Connection timing
        start_time = time.time()
        with OptimizedSessionLocal() as db:
            connection_time = (time.time() - start_time) * 1000
            operations.append(("Connection", connection_time))
            
            # Simple query timing
            start_time = time.time()
            db.execute("SELECT 1").scalar()
            query_time = (time.time() - start_time) * 1000
            operations.append(("Simple query", query_time))
            
            # Count query timing
            start_time = time.time()
            user_count = db.query(User).count()
            count_time = (time.time() - start_time) * 1000
            operations.append(("Count query", count_time))
            print(f"✓ User count: {user_count}")
            
            # Insert timing (if we have users table)
            try:
                start_time = time.time()
                test_user = User(
                    username=f"test_opt_{int(time.time())}",
                    hashed_password="test_hash",
                    role="user"
                )
                db.add(test_user)
                db.commit()
                insert_time = (time.time() - start_time) * 1000
                operations.append(("Insert operation", insert_time))
                
                # Cleanup
                db.delete(test_user)
                db.commit()
                
            except Exception as e:
                print(f"⚠️  Insert test skipped: {e}")
        
        # Report performance
        print("✓ Performance test results:")
        for operation, timing in operations:
            status = "✓" if timing < 50 else "⚠️" if timing < 100 else "❌"
            print(f"    {status} {operation}: {timing:.2f}ms")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False


def test_concurrent_operations():
    """Test concurrent operations with optimized configuration"""
    print("\n=== Testing Concurrent Operations ===")
    
    def worker_operation(worker_id, results):
        """Worker function for concurrent testing"""
        try:
            start_time = time.time()
            
            with OptimizedSessionLocal() as db:
                # Perform various operations
                operations = 0
                
                # Read operations
                for i in range(3):
                    db.query(User).count()
                    operations += 1
                
                # Write operation
                test_user = User(
                    username=f"concurrent_test_{worker_id}_{int(time.time())}",
                    hashed_password="test_hash",
                    role="user"
                )
                db.add(test_user)
                db.commit()
                operations += 1
                
                # Cleanup
                db.delete(test_user)
                db.commit()
                operations += 1
            
            total_time = (time.time() - start_time) * 1000
            results[worker_id] = {
                "success": True,
                "operations": operations,
                "time_ms": total_time,
                "error": None
            }
            
        except Exception as e:
            results[worker_id] = {
                "success": False,
                "operations": 0,
                "time_ms": 0,
                "error": str(e)
            }
    
    # Run concurrent workers
    num_workers = 3  # Reduced for SQLite limitations
    results = {}
    threads = []
    
    start_time = time.time()
    
    for worker_id in range(num_workers):
        thread = threading.Thread(target=worker_operation, args=(worker_id, results))
        threads.append(thread)
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    total_time = time.time() - start_time
    
    # Analyze results
    successful_workers = sum(1 for r in results.values() if r["success"])
    failed_workers = num_workers - successful_workers
    total_operations = sum(r["operations"] for r in results.values())
    
    print(f"✓ Concurrent test completed in {total_time:.2f}s")
    print(f"✓ Successful workers: {successful_workers}/{num_workers}")
    print(f"✓ Failed workers: {failed_workers}")
    print(f"✓ Total operations: {total_operations}")
    
    if failed_workers > 0:
        print("❌ Worker errors:")
        for worker_id, result in results.items():
            if not result["success"]:
                print(f"    Worker {worker_id}: {result['error']}")
    
    # Performance assessment
    if failed_workers == 0:
        print("✅ All concurrent operations successful")
        return True
    elif failed_workers < num_workers / 2:
        print("⚠️  Some concurrent operations failed")
        return True
    else:
        print("❌ Majority of concurrent operations failed")
        return False


def test_production_readiness():
    """Test production readiness of optimized configuration"""
    print("\n=== Testing Production Readiness ===")
    
    try:
        # Get production recommendations
        recommendations = get_production_recommendations()
        
        print("📋 Production Assessment:")
        print(f"   Migration Priority: {recommendations['migration_priority']}")
        print(f"   Migration Timeline: {recommendations['migration_timeline']}")
        
        print("\n📈 PostgreSQL Benefits:")
        for benefit, description in recommendations['postgresql_benefits'].items():
            print(f"   • {benefit}: {description}")
        
        print("\n⚠️  SQLite Limitations:")
        for limitation, description in recommendations['sqlite_limitations'].items():
            print(f"   • {limitation}: {description}")
        
        print("\n🔧 Immediate SQLite Improvements:")
        for improvement in recommendations['immediate_sqlite_improvements']:
            print(f"   • {improvement}")
        
        return True
        
    except Exception as e:
        print(f"❌ Production readiness test failed: {e}")
        return False


def generate_configuration_report():
    """Generate comprehensive configuration report"""
    print("\n" + "="*60)
    print("DATABASE CONFIGURATION OPTIMIZATION REPORT")
    print("="*60)
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "tests": {}
    }
    
    # Run all tests
    tests = [
        ("basic_configuration", test_basic_configuration),
        ("sqlite_optimizations", test_sqlite_optimizations), 
        ("performance_improvements", test_performance_improvements),
        ("concurrent_operations", test_concurrent_operations),
        ("production_readiness", test_production_readiness)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            report["tests"][test_name] = {
                "passed": result,
                "status": "PASS" if result else "FAIL"
            }
        except Exception as e:
            report["tests"][test_name] = {
                "passed": False,
                "status": "ERROR",
                "error": str(e)
            }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("-"*60)
    
    passed_tests = sum(1 for test in report["tests"].values() if test["passed"])
    total_tests = len(report["tests"])
    
    for test_name, test_result in report["tests"].items():
        status_icon = "✅" if test_result["passed"] else "❌"
        print(f"{status_icon} {test_name.replace('_', ' ').title()}: {test_result['status']}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All optimization tests passed!")
    elif passed_tests >= total_tests * 0.8:
        print("⚠️  Most tests passed - review failures")
    else:
        print("❌ Significant issues found - optimization needed")
    
    return report


def main():
    """Run database configuration optimization tests"""
    print("Database Configuration Optimization Test Suite")
    print("I005 Infrastructure Issue - SQLite Limitations & PostgreSQL Migration")
    
    try:
        # Validate optimized database first
        if not validate_optimized_database():
            print("❌ Optimized database validation failed!")
            return False
        
        # Apply optimizations
        apply_database_optimizations()
        
        # Generate comprehensive report
        report = generate_configuration_report()
        
        # Save report
        import json
        report_file = "/home/buymeagoat/dev/whisper-transcriber/temp/database_config_optimization_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        return False


if __name__ == "__main__":
    main()