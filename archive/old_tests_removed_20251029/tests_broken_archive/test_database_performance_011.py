#!/usr/bin/env python3

"""
Database Performance Testing Suite
Comprehensive tests to validate database optimization improvements and benchmarks
"""

import time
import statistics
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.models import Base, Job, User, TranscriptMetadata, AuditLog, JobStatusEnum
from api.query_optimizer import (
    OptimizedJobQueries,
    OptimizedUserQueries,
    OptimizedMetadataQueries,
    OptimizedAuditLogQueries,
    QueryPerformanceMonitor
)


class DatabasePerformanceTester:
    """Comprehensive database performance testing framework"""
    
    def __init__(self, database_url: str = "sqlite:///:memory:"):
        self.engine = create_engine(
            database_url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
        # Performance tracking
        self.performance_results = {}
        self.monitor = QueryPerformanceMonitor(slow_query_threshold_ms=50.0)
    
    @contextmanager
    def get_db_session(self):
        """Get database session for testing"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @contextmanager
    def time_operation(self, operation_name: str):
        """Time an operation and store results"""
        start_time = time.time()
        yield
        execution_time = time.time() - start_time
        
        if operation_name not in self.performance_results:
            self.performance_results[operation_name] = []
        self.performance_results[operation_name].append(execution_time * 1000)  # Store in ms
    
    def generate_test_data(self, num_users: int = 100, num_jobs: int = 1000, num_metadata: int = 500):
        """Generate test data for performance testing"""
        
        with self.get_db_session() as db:
            print(f"Generating test data: {num_users} users, {num_jobs} jobs, {num_metadata} metadata records...")
            
            # Generate users
            users = []
            for i in range(num_users):
                user = User(
                    username=f"user_{i:04d}",
                    hashed_password=f"hash_{i}",
                    role="admin" if i < 5 else "user",
                    is_active=True,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365)),
                    last_login=datetime.utcnow() - timedelta(days=random.randint(0, 30)) if random.random() > 0.2 else None
                )
                users.append(user)
                db.add(user)
            
            db.flush()  # Get user IDs
            
            # Generate jobs
            statuses = list(JobStatusEnum)
            models = ["tiny", "small", "medium", "large"]
            
            for i in range(num_jobs):
                user = random.choice(users)
                status = random.choice(statuses)
                created_at = datetime.utcnow() - timedelta(days=random.randint(0, 180))
                
                # Calculate realistic timing
                started_at = None
                finished_at = None
                processing_time = None
                
                if status in [JobStatusEnum.PROCESSING, JobStatusEnum.COMPLETED, JobStatusEnum.FAILED]:
                    started_at = created_at + timedelta(minutes=random.randint(0, 60))
                    
                if status in [JobStatusEnum.COMPLETED, JobStatusEnum.FAILED]:
                    processing_time = random.uniform(30, 1800)  # 30 seconds to 30 minutes
                    finished_at = started_at + timedelta(seconds=processing_time)
                
                job = Job(
                    id=f"job_{i:06d}",
                    original_filename=f"audio_{i:06d}.{''.join(random.choices(string.ascii_lowercase, k=3))}",
                    saved_filename=f"saved_{i:06d}.wav",
                    model=random.choice(models),
                    status=status,
                    user_id=user.id,
                    created_at=created_at,
                    updated_at=created_at + timedelta(minutes=random.randint(0, 10)),
                    started_at=started_at,
                    finished_at=finished_at,
                    processing_time_seconds=processing_time,
                    file_size_bytes=random.randint(1024*1024, 100*1024*1024),  # 1MB to 100MB
                    duration_seconds=random.uniform(60, 3600)  # 1 minute to 1 hour
                )
                db.add(job)
            
            db.flush()  # Get job IDs
            
            # Generate metadata for completed jobs
            completed_jobs = db.query(Job).filter(Job.status == JobStatusEnum.COMPLETED).limit(num_metadata).all()
            
            for job in completed_jobs:
                duration = int(job.duration_seconds or random.randint(60, 3600))
                tokens = random.randint(100, 10000)
                wpm = random.randint(120, 200)
                
                metadata = TranscriptMetadata(
                    job_id=job.id,
                    tokens=tokens,
                    duration=duration,
                    abstract=f"This is a sample abstract for job {job.id}",
                    sample_rate=random.choice([16000, 22050, 44100, 48000]),
                    wpm=wpm,
                    keywords="speech, audio, transcription",
                    summary=f"Summary of transcription for {job.original_filename}",
                    language=random.choice(["en", "es", "fr", "de", "it", "pt"]),
                    sentiment=random.uniform(-1.0, 1.0),
                    generated_at=job.finished_at or datetime.utcnow()
                )
                db.add(metadata)
            
            # Generate audit logs
            for i in range(num_jobs * 2):  # 2 audit entries per job on average
                user = random.choice(users)
                timestamp = datetime.utcnow() - timedelta(days=random.randint(0, 90))
                
                audit = AuditLog(
                    timestamp=timestamp,
                    event_type=random.choice(["login", "logout", "job_created", "job_completed", "api_access"]),
                    severity=random.choice(["low", "medium", "high"]),
                    user_id=user.id,
                    username=user.username,
                    client_ip=f"192.168.1.{random.randint(1, 254)}",
                    endpoint=random.choice(["/jobs", "/upload", "/admin", "/login", "/dashboard"]),
                    method=random.choice(["GET", "POST", "PUT", "DELETE"]),
                    status_code=random.choice([200, 201, 400, 401, 403, 404, 500]),
                    session_id=f"session_{random.randint(1000, 9999)}"
                )
                db.add(audit)
            
            db.commit()
            print("Test data generation completed!")


class TestDatabasePerformanceOptimizations:
    """Test suite for database performance optimizations"""
    
    @pytest.fixture(scope="class")
    def performance_tester(self):
        """Setup performance testing environment"""
        tester = DatabasePerformanceTester()
        tester.generate_test_data(num_users=50, num_jobs=500, num_metadata=250)
        return tester
    
    def test_job_listing_performance(self, performance_tester):
        """Test job listing performance with different approaches"""
        
        with performance_tester.get_db_session() as db:
            # Test original approach (N+1 queries)
            with performance_tester.time_operation("job_listing_original"):
                jobs = db.query(Job).order_by(Job.created_at.desc()).limit(20).all()
                # Simulate N+1 by accessing user for each job
                for job in jobs:
                    if job.user_id:
                        user = db.query(User).filter(User.id == job.user_id).first()
            
            # Test optimized approach
            with performance_tester.time_operation("job_listing_optimized"):
                jobs, total = OptimizedJobQueries.get_jobs_by_user_paginated(
                    db=db, user_id=1, page=1, page_size=20
                )
        
        # Verify optimized is faster
        original_times = performance_tester.performance_results["job_listing_original"]
        optimized_times = performance_tester.performance_results["job_listing_optimized"]
        
        assert statistics.mean(optimized_times) < statistics.mean(original_times)
        print(f"Job listing optimization: {statistics.mean(original_times):.2f}ms → {statistics.mean(optimized_times):.2f}ms")
    
    def test_job_statistics_performance(self, performance_tester):
        """Test job statistics performance"""
        
        with performance_tester.get_db_session() as db:
            # Test original approach (multiple queries)
            with performance_tester.time_operation("job_stats_original"):
                total_jobs = db.query(Job).count()
                completed_jobs = db.query(Job).filter(Job.status == JobStatusEnum.COMPLETED).count()
                failed_jobs = db.query(Job).filter(Job.status == JobStatusEnum.FAILED).count()
                avg_processing = db.query(func.avg(Job.processing_time_seconds)).scalar()
            
            # Test optimized approach (single aggregation query)
            with performance_tester.time_operation("job_stats_optimized"):
                stats = OptimizedJobQueries.get_job_statistics(db=db, days=30)
        
        # Verify optimized is faster
        original_times = performance_tester.performance_results["job_stats_original"]
        optimized_times = performance_tester.performance_results["job_stats_optimized"]
        
        assert statistics.mean(optimized_times) < statistics.mean(original_times)
        print(f"Job statistics optimization: {statistics.mean(original_times):.2f}ms → {statistics.mean(optimized_times):.2f}ms")
    
    def test_user_activity_performance(self, performance_tester):
        """Test user activity query performance"""
        
        with performance_tester.get_db_session() as db:
            # Test optimized user activity query
            with performance_tester.time_operation("user_activity_optimized"):
                activity = OptimizedAuditLogQueries.get_user_activity_summary(db=db, user_id=1, days=7)
            
            # Verify results are meaningful
            assert isinstance(activity, dict)
            assert "total_events" in activity
            print(f"User activity query: {statistics.mean(performance_tester.performance_results['user_activity_optimized']):.2f}ms")
    
    def test_metadata_analytics_performance(self, performance_tester):
        """Test metadata analytics performance"""
        
        with performance_tester.get_db_session() as db:
            # Test optimized metadata analytics
            with performance_tester.time_operation("metadata_analytics_optimized"):
                analytics = OptimizedMetadataQueries.get_metadata_analytics(db=db, days=30)
            
            # Verify results
            assert isinstance(analytics, dict)
            assert "total_transcripts" in analytics
            print(f"Metadata analytics query: {statistics.mean(performance_tester.performance_results['metadata_analytics_optimized']):.2f}ms")
    
    def test_search_performance(self, performance_tester):
        """Test search query performance"""
        
        with performance_tester.get_db_session() as db:
            # Test search with filters
            with performance_tester.time_operation("search_jobs"):
                search_query = db.query(Job).filter(
                    Job.original_filename.ilike("%audio%")
                ).order_by(Job.created_at.desc()).limit(20)
                results = search_query.all()
            
            assert len(results) > 0
            print(f"Search query: {statistics.mean(performance_tester.performance_results['search_jobs']):.2f}ms")
    
    def test_pagination_performance(self, performance_tester):
        """Test pagination performance with large datasets"""
        
        with performance_tester.get_db_session() as db:
            # Test pagination at different offsets
            page_sizes = [10, 20, 50]
            pages = [1, 5, 10, 20]
            
            for page_size in page_sizes:
                for page in pages:
                    offset = (page - 1) * page_size
                    
                    with performance_tester.time_operation(f"pagination_{page_size}_{page}"):
                        jobs = db.query(Job).order_by(Job.created_at.desc()).offset(offset).limit(page_size).all()
                    
                    assert len(jobs) <= page_size
    
    def test_index_effectiveness(self, performance_tester):
        """Test that indexes are being used effectively"""
        
        with performance_tester.get_db_session() as db:
            # Test queries that should use indexes
            test_queries = [
                ("user_lookup", lambda: db.query(User).filter(User.username == "user_0001").first()),
                ("job_by_status", lambda: db.query(Job).filter(Job.status == JobStatusEnum.COMPLETED).count()),
                ("job_by_user", lambda: db.query(Job).filter(Job.user_id == 1).count()),
                ("recent_jobs", lambda: db.query(Job).order_by(Job.created_at.desc()).limit(10).all()),
                ("audit_by_user", lambda: db.query(AuditLog).filter(AuditLog.user_id == 1).count()),
            ]
            
            for query_name, query_func in test_queries:
                with performance_tester.time_operation(query_name):
                    result = query_func()
                
                # Verify reasonable performance (should be fast with indexes)
                avg_time = statistics.mean(performance_tester.performance_results[query_name])
                assert avg_time < 50, f"{query_name} took {avg_time:.2f}ms, may not be using indexes"
                print(f"{query_name}: {avg_time:.2f}ms")


class BenchmarkRunner:
    """Run comprehensive database performance benchmarks"""
    
    def __init__(self):
        self.tester = DatabasePerformanceTester()
    
    def run_baseline_benchmarks(self) -> Dict[str, Any]:
        """Run baseline performance benchmarks"""
        
        print("Running baseline database performance benchmarks...")
        
        # Generate test data
        self.tester.generate_test_data(num_users=100, num_jobs=1000, num_metadata=500)
        
        benchmarks = {}
        
        with self.tester.get_db_session() as db:
            # Benchmark 1: Basic CRUD operations
            with self.tester.time_operation("create_user"):
                user = User(username="benchmark_user", hashed_password="hash", role="user")
                db.add(user)
                db.commit()
            
            with self.tester.time_operation("read_user"):
                user = db.query(User).filter(User.username == "benchmark_user").first()
            
            with self.tester.time_operation("update_user"):
                user.last_login = datetime.utcnow()
                db.commit()
            
            # Benchmark 2: Complex queries
            with self.tester.time_operation("complex_job_query"):
                stats = OptimizedJobQueries.get_job_statistics(db=db, days=30)
            
            with self.tester.time_operation("paginated_job_list"):
                jobs, total = OptimizedJobQueries.get_jobs_by_user_paginated(db=db, user_id=1, page=1, page_size=50)
            
            # Benchmark 3: Analytics queries
            with self.tester.time_operation("metadata_analytics"):
                analytics = OptimizedMetadataQueries.get_metadata_analytics(db=db, days=30)
            
            with self.tester.time_operation("audit_analysis"):
                activity = OptimizedAuditLogQueries.get_user_activity_summary(db=db, user_id=1, days=7)
        
        # Compile results
        for operation, times in self.tester.performance_results.items():
            benchmarks[operation] = {
                "avg_ms": statistics.mean(times),
                "min_ms": min(times),
                "max_ms": max(times),
                "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
                "runs": len(times)
            }
        
        return benchmarks
    
    def run_stress_test(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """Run stress test to identify performance limits"""
        
        print(f"Running stress test for {duration_seconds} seconds...")
        
        start_time = time.time()
        operations = 0
        errors = 0
        
        while time.time() - start_time < duration_seconds:
            try:
                with self.tester.get_db_session() as db:
                    # Random operations
                    operation_type = random.choice([
                        "job_stats",
                        "user_lookup", 
                        "job_listing",
                        "metadata_query"
                    ])
                    
                    if operation_type == "job_stats":
                        OptimizedJobQueries.get_job_statistics(db=db, days=30)
                    elif operation_type == "user_lookup":
                        db.query(User).filter(User.id == random.randint(1, 50)).first()
                    elif operation_type == "job_listing":
                        OptimizedJobQueries.get_jobs_by_user_paginated(
                            db=db, user_id=random.randint(1, 50), page=1, page_size=20
                        )
                    elif operation_type == "metadata_query":
                        OptimizedMetadataQueries.get_metadata_analytics(db=db, days=7)
                    
                operations += 1
                
            except Exception as e:
                errors += 1
                print(f"Error in stress test: {e}")
        
        actual_duration = time.time() - start_time
        
        return {
            "duration_seconds": actual_duration,
            "total_operations": operations,
            "operations_per_second": operations / actual_duration,
            "error_count": errors,
            "error_rate": errors / max(operations, 1) * 100
        }


def main():
    """Run database performance tests and benchmarks"""
    
    print("Database Performance Testing Suite")
    print("=" * 50)
    
    # Run unit tests
    print("\nRunning performance unit tests...")
    pytest.main([__file__, "-v", "--tb=short"])
    
    # Run benchmarks
    print("\nRunning performance benchmarks...")
    runner = BenchmarkRunner()
    
    # Baseline benchmarks
    benchmarks = runner.run_baseline_benchmarks()
    
    print("\nBaseline Performance Results:")
    print("-" * 30)
    for operation, stats in benchmarks.items():
        print(f"{operation:25}: {stats['avg_ms']:6.2f}ms (±{stats['std_dev']:5.2f})")
    
    # Stress test
    print("\nRunning stress test...")
    stress_results = runner.run_stress_test(duration_seconds=30)
    
    print(f"\nStress Test Results:")
    print(f"Operations/second: {stress_results['operations_per_second']:.1f}")
    print(f"Total operations: {stress_results['total_operations']}")
    print(f"Error rate: {stress_results['error_rate']:.2f}%")
    
    # Performance recommendations
    print("\nPerformance Recommendations:")
    print("-" * 30)
    
    slow_operations = [(op, stats) for op, stats in benchmarks.items() if stats['avg_ms'] > 100]
    if slow_operations:
        print("❌ Slow operations detected:")
        for op, stats in slow_operations:
            print(f"  - {op}: {stats['avg_ms']:.2f}ms")
    else:
        print("✅ All operations performing well (<100ms)")
    
    if stress_results['operations_per_second'] > 100:
        print("✅ Good throughput performance")
    else:
        print("⚠️  Consider additional optimization for high-load scenarios")
    
    if stress_results['error_rate'] < 1:
        print("✅ Low error rate under stress")
    else:
        print("❌ High error rate under stress - investigate stability issues")


if __name__ == "__main__":
    main()
