#!/usr/bin/env python3

"""
Database Performance Analysis - I005 Infrastructure Issue
Analyzes current SQLite database performance, connection pooling, and concurrent load limitations
"""

import os
import sys
import time
import threading
import statistics
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Dict, List, Any, Optional

# Add the project root to the path
sys.path.insert(0, '/home/buymeagoat/dev/whisper-transcriber')

from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.orm_bootstrap import Base, engine, SessionLocal, get_database_info
from api.models import Job, User, TranscriptMetadata, AuditLog, JobStatusEnum
from api.settings import settings
from api.utils.logger import get_system_logger

logger = get_system_logger("db_analysis")


class DatabasePerformanceAnalyzer:
    """Comprehensive database performance analysis for I005"""
    
    def __init__(self):
        self.results = {}
        self.concurrent_results = {}
        
    def analyze_current_configuration(self) -> Dict[str, Any]:
        """Analyze current database configuration and setup"""
        logger.info("Analyzing current database configuration...")
        
        config_analysis = {
            "database_type": "SQLite" if "sqlite" in settings.database_url else "Other",
            "database_url": settings.database_url,
            "connection_pooling": {
                "enabled": hasattr(engine.pool, 'size'),
                "pool_class": str(type(engine.pool).__name__),
                "pool_size": getattr(engine.pool, '_pool_size', 'N/A'),
                "max_overflow": getattr(engine.pool, '_max_overflow', 'N/A'),
            },
            "engine_configuration": {
                "echo": engine.echo,
                "connect_args": getattr(engine, 'connect_args', {}),
            }
        }
        
        # Get database info
        db_info = get_database_info()
        config_analysis["database_info"] = db_info
        
        # Check database file size
        if "sqlite" in settings.database_url:
            db_file_path = settings.database_url.replace("sqlite:///", "").replace("sqlite://", "")
            if os.path.exists(db_file_path):
                file_size = os.path.getsize(db_file_path)
                config_analysis["database_file_size_mb"] = file_size / (1024 * 1024)
            else:
                config_analysis["database_file_size_mb"] = 0
        
        return config_analysis
    
    def analyze_table_structure(self) -> Dict[str, Any]:
        """Analyze database table structure and indexes"""
        logger.info("Analyzing table structure and indexes...")
        
        table_analysis = {}
        
        with SessionLocal() as db:
            try:
                # For SQLite, analyze table structure
                if "sqlite" in settings.database_url:
                    tables = ['users', 'jobs', 'transcript_metadata', 'audit_logs', 'performance_metrics']
                    
                    for table in tables:
                        try:
                            # Get table info
                            table_info = db.execute(text(f"PRAGMA table_info({table})")).fetchall()
                            
                            # Get index info
                            index_info = db.execute(text(f"PRAGMA index_list({table})")).fetchall()
                            
                            # Get row count
                            row_count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                            
                            table_analysis[table] = {
                                "columns": len(table_info),
                                "indexes": len(index_info),
                                "row_count": row_count,
                                "index_details": [dict(row._mapping) for row in index_info] if index_info else []
                            }
                            
                        except Exception as e:
                            table_analysis[table] = {"error": str(e)}
                            
            except Exception as e:
                table_analysis["error"] = str(e)
        
        return table_analysis
    
    def benchmark_basic_operations(self, iterations: int = 100) -> Dict[str, Any]:
        """Benchmark basic database operations"""
        logger.info(f"Benchmarking basic operations ({iterations} iterations)...")
        
        operation_times = {
            "connection_time": [],
            "simple_select": [],
            "join_query": [],
            "aggregation_query": [],
            "insert_operation": [],
            "update_operation": []
        }
        
        for i in range(iterations):
            try:
                # Test connection time
                start_time = time.time()
                with SessionLocal() as db:
                    connection_time = (time.time() - start_time) * 1000
                    operation_times["connection_time"].append(connection_time)
                    
                    # Simple select
                    start_time = time.time()
                    db.execute(text("SELECT 1")).scalar()
                    operation_times["simple_select"].append((time.time() - start_time) * 1000)
                    
                    # Check if we have data before running complex queries
                    user_count = db.query(User).count()
                    job_count = db.query(Job).count()
                    
                    if user_count > 0 and job_count > 0:
                        # Join query
                        start_time = time.time()
                        result = db.query(Job).join(User).limit(5).all()
                        operation_times["join_query"].append((time.time() - start_time) * 1000)
                        
                        # Aggregation query
                        start_time = time.time()
                        db.query(func.count(Job.id)).scalar()
                        operation_times["aggregation_query"].append((time.time() - start_time) * 1000)
                    
                    # Insert operation (test user)
                    start_time = time.time()
                    test_user = User(
                        username=f"test_perf_{i}_{int(time.time())}",
                        hashed_password="test_hash",
                        role="user"
                    )
                    db.add(test_user)
                    db.commit()
                    operation_times["insert_operation"].append((time.time() - start_time) * 1000)
                    
                    # Update operation
                    start_time = time.time()
                    test_user.role = "admin"
                    db.commit()
                    operation_times["update_operation"].append((time.time() - start_time) * 1000)
                    
                    # Cleanup
                    db.delete(test_user)
                    db.commit()
                    
            except Exception as e:
                logger.error(f"Error in iteration {i}: {e}")
                continue
        
        # Calculate statistics
        benchmark_results = {}
        for operation, times in operation_times.items():
            if times:
                benchmark_results[operation] = {
                    "avg_ms": statistics.mean(times),
                    "min_ms": min(times),
                    "max_ms": max(times),
                    "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
                    "median_ms": statistics.median(times),
                    "samples": len(times)
                }
            else:
                benchmark_results[operation] = {"error": "No successful operations"}
        
        return benchmark_results
    
    def test_concurrent_operations(self, num_threads: int = 10, operations_per_thread: int = 20) -> Dict[str, Any]:
        """Test concurrent database operations to identify bottlenecks"""
        logger.info(f"Testing concurrent operations ({num_threads} threads, {operations_per_thread} ops each)...")
        
        results = {
            "thread_results": [],
            "errors": [],
            "total_operations": 0,
            "successful_operations": 0,
            "total_time_seconds": 0
        }
        
        def worker_thread(thread_id: int):
            """Worker thread for concurrent operations"""
            thread_results = {
                "thread_id": thread_id,
                "operations": 0,
                "errors": 0,
                "avg_operation_time": 0,
                "operation_times": []
            }
            
            try:
                for i in range(operations_per_thread):
                    operation_start = time.time()
                    
                    try:
                        with SessionLocal() as db:
                            # Mix of operations
                            operation_type = i % 4
                            
                            if operation_type == 0:
                                # Read operation
                                db.query(User).count()
                            elif operation_type == 1:
                                # Write operation
                                test_user = User(
                                    username=f"thread_{thread_id}_op_{i}_{int(time.time())}",
                                    hashed_password="hash",
                                    role="user"
                                )
                                db.add(test_user)
                                db.commit()
                                # Cleanup immediately
                                db.delete(test_user)
                                db.commit()
                            elif operation_type == 2:
                                # Aggregation
                                db.query(func.count(Job.id)).scalar()
                            else:
                                # Complex query
                                db.execute(text("SELECT COUNT(*) FROM users WHERE role = 'user'")).scalar()
                        
                        operation_time = (time.time() - operation_start) * 1000
                        thread_results["operation_times"].append(operation_time)
                        thread_results["operations"] += 1
                        
                    except Exception as e:
                        thread_results["errors"] += 1
                        results["errors"].append(f"Thread {thread_id}, Op {i}: {str(e)}")
                
                # Calculate thread statistics
                if thread_results["operation_times"]:
                    thread_results["avg_operation_time"] = statistics.mean(thread_results["operation_times"])
                
            except Exception as e:
                results["errors"].append(f"Thread {thread_id} fatal error: {str(e)}")
            
            return thread_results
        
        # Run concurrent operations
        start_time = time.time()
        threads = []
        
        for thread_id in range(num_threads):
            thread = threading.Thread(target=lambda tid=thread_id: results["thread_results"].append(worker_thread(tid)))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        results["total_time_seconds"] = time.time() - start_time
        
        # Calculate overall statistics
        total_ops = sum(tr.get("operations", 0) for tr in results["thread_results"])
        results["total_operations"] = total_ops
        results["successful_operations"] = total_ops - sum(tr.get("errors", 0) for tr in results["thread_results"])
        
        if results["total_time_seconds"] > 0:
            results["operations_per_second"] = results["successful_operations"] / results["total_time_seconds"]
        
        # Overall performance statistics
        all_operation_times = []
        for tr in results["thread_results"]:
            all_operation_times.extend(tr.get("operation_times", []))
        
        if all_operation_times:
            results["overall_performance"] = {
                "avg_operation_time_ms": statistics.mean(all_operation_times),
                "min_operation_time_ms": min(all_operation_times),
                "max_operation_time_ms": max(all_operation_times),
                "std_dev": statistics.stdev(all_operation_times),
                "median_operation_time_ms": statistics.median(all_operation_times)
            }
        
        return results
    
    def analyze_sqlite_limitations(self) -> Dict[str, Any]:
        """Analyze SQLite-specific limitations and concurrent performance"""
        logger.info("Analyzing SQLite limitations...")
        
        limitations = {
            "concurrent_write_support": False,  # SQLite only supports one writer at a time
            "connection_sharing": "limited",  # SQLite has limited connection sharing
            "transaction_isolation": "serializable_by_default",
            "write_ahead_logging": None,
            "foreign_key_support": None,
            "max_connections": "no_hard_limit_but_performance_degrades"
        }
        
        try:
            with SessionLocal() as db:
                # Check WAL mode
                wal_result = db.execute(text("PRAGMA journal_mode")).scalar()
                limitations["write_ahead_logging"] = wal_result
                
                # Check foreign key support
                fk_result = db.execute(text("PRAGMA foreign_keys")).scalar()
                limitations["foreign_key_support"] = bool(fk_result)
                
                # Check other SQLite settings
                cache_size = db.execute(text("PRAGMA cache_size")).scalar()
                page_size = db.execute(text("PRAGMA page_size")).scalar()
                synchronous = db.execute(text("PRAGMA synchronous")).scalar()
                
                limitations["current_settings"] = {
                    "cache_size": cache_size,
                    "page_size": page_size,
                    "synchronous": synchronous,
                    "journal_mode": wal_result
                }
                
        except Exception as e:
            limitations["analysis_error"] = str(e)
        
        # SQLite known limitations
        limitations["known_limitations"] = {
            "single_writer": "Only one write transaction at a time",
            "table_locks": "Table-level locking can cause contention",
            "concurrent_reads": "Multiple readers OK, but writers block everything",
            "no_connection_pooling": "Connection pooling limited effectiveness",
            "file_based": "File I/O can be bottleneck on high concurrency",
            "no_built_in_replication": "No horizontal scaling capability"
        }
        
        return limitations
    
    def generate_recommendations(self, config: Dict, benchmarks: Dict, concurrent: Dict, limitations: Dict) -> Dict[str, List[str]]:
        """Generate specific recommendations based on analysis"""
        logger.info("Generating performance recommendations...")
        
        recommendations = {
            "immediate_improvements": [],
            "sqlite_optimizations": [],
            "postgresql_migration_benefits": [],
            "monitoring_improvements": [],
            "configuration_changes": []
        }
        
        # Analyze benchmarks for immediate improvements
        if benchmarks:
            avg_connection_time = benchmarks.get("connection_time", {}).get("avg_ms", 0)
            if avg_connection_time > 10:
                recommendations["immediate_improvements"].append(
                    f"Connection time is {avg_connection_time:.1f}ms - consider connection pooling optimization"
                )
            
            avg_insert_time = benchmarks.get("insert_operation", {}).get("avg_ms", 0)
            if avg_insert_time > 50:
                recommendations["immediate_improvements"].append(
                    f"Insert operations averaging {avg_insert_time:.1f}ms - consider batch operations"
                )
        
        # Analyze concurrent performance
        if concurrent:
            ops_per_second = concurrent.get("operations_per_second", 0)
            error_count = len(concurrent.get("errors", []))
            
            if ops_per_second < 100:
                recommendations["immediate_improvements"].append(
                    f"Low throughput: {ops_per_second:.1f} ops/sec - investigate bottlenecks"
                )
            
            if error_count > 0:
                recommendations["immediate_improvements"].append(
                    f"{error_count} errors in concurrent testing - review error patterns"
                )
        
        # SQLite specific optimizations
        current_settings = limitations.get("current_settings", {})
        
        if current_settings.get("journal_mode") != "wal":
            recommendations["sqlite_optimizations"].append(
                "Enable WAL mode: PRAGMA journal_mode=WAL for better concurrent reads"
            )
        
        if current_settings.get("synchronous", 0) > 1:
            recommendations["sqlite_optimizations"].append(
                "Consider PRAGMA synchronous=NORMAL for better performance"
            )
        
        cache_size = current_settings.get("cache_size", 0)
        if abs(cache_size) < 10000:  # SQLite cache_size can be negative (KB) or positive (pages)
            recommendations["sqlite_optimizations"].append(
                "Increase cache size: PRAGMA cache_size=-64000 (64MB cache)"
            )
        
        # PostgreSQL migration benefits
        recommendations["postgresql_migration_benefits"] = [
            "True concurrent writes - no single-writer limitation",
            "Advanced connection pooling with pgbouncer/pgpool",
            "Better query optimization and execution plans",
            "Native JSON support and advanced indexing",
            "Horizontal scaling with read replicas",
            "Advanced monitoring and performance tools",
            "Better handling of high-concurrency workloads",
            "MVCC (Multi-Version Concurrency Control) for better isolation"
        ]
        
        # Monitoring improvements
        recommendations["monitoring_improvements"] = [
            "Implement query performance logging",
            "Add connection pool monitoring",
            "Set up slow query alerts (>100ms threshold)",
            "Monitor concurrent operation success rates",
            "Track database file size growth",
            "Implement automated performance regression testing"
        ]
        
        # Configuration improvements
        if config.get("database_type") == "SQLite":
            recommendations["configuration_changes"] = [
                "Add WAL mode to database URL: sqlite:///./app.db?mode=wal",
                "Configure connection pool with StaticPool for SQLite",
                "Set up proper connection timeouts",
                "Consider read-only connection pool for reporting queries",
                "Implement connection lifecycle management"
            ]
        
        return recommendations
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete database performance analysis"""
        logger.info("Starting comprehensive database performance analysis...")
        
        analysis_results = {
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "configuration": self.analyze_current_configuration(),
            "table_structure": self.analyze_table_structure(),
            "benchmark_results": self.benchmark_basic_operations(50),
            "concurrent_performance": self.test_concurrent_operations(5, 10),  # Reduced for faster testing
            "sqlite_limitations": self.analyze_sqlite_limitations()
        }
        
        # Generate recommendations based on analysis
        analysis_results["recommendations"] = self.generate_recommendations(
            analysis_results["configuration"],
            analysis_results["benchmark_results"],
            analysis_results["concurrent_performance"],
            analysis_results["sqlite_limitations"]
        )
        
        return analysis_results


def main():
    """Run database performance analysis"""
    print("Database Performance Analysis - I005 Infrastructure Issue")
    print("=" * 60)
    
    analyzer = DatabasePerformanceAnalyzer()
    
    try:
        results = analyzer.run_full_analysis()
        
        # Print summary
        print("\nANALYSIS SUMMARY")
        print("-" * 30)
        
        config = results.get("configuration", {})
        print(f"Database Type: {config.get('database_type', 'Unknown')}")
        print(f"Database Size: {config.get('database_file_size_mb', 0):.2f} MB")
        
        benchmarks = results.get("benchmark_results", {})
        if benchmarks:
            print("\nPerformance Benchmarks:")
            for operation, stats in benchmarks.items():
                if isinstance(stats, dict) and "avg_ms" in stats:
                    print(f"  {operation}: {stats['avg_ms']:.2f}ms avg")
        
        concurrent = results.get("concurrent_performance", {})
        if concurrent:
            print(f"\nConcurrent Performance:")
            print(f"  Operations/second: {concurrent.get('operations_per_second', 0):.1f}")
            print(f"  Error count: {len(concurrent.get('errors', []))}")
        
        # Print recommendations
        recommendations = results.get("recommendations", {})
        print("\nIMMEDIATE RECOMMENDATIONS:")
        for rec in recommendations.get("immediate_improvements", [])[:3]:
            print(f"  • {rec}")
        
        print("\nSQLITE OPTIMIZATIONS:")
        for rec in recommendations.get("sqlite_optimizations", [])[:3]:
            print(f"  • {rec}")
        
        print("\nPOSTGRESQL MIGRATION BENEFITS:")
        for rec in recommendations.get("postgresql_migration_benefits", [])[:3]:
            print(f"  • {rec}")
        
        # Save detailed results
        import json
        output_file = "/home/buymeagoat/dev/whisper-transcriber/temp/database_analysis_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nDetailed results saved to: {output_file}")
        
        return results
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"❌ Analysis failed: {e}")
        return None


if __name__ == "__main__":
    main()