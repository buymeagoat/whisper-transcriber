#!/usr/bin/env python3

"""
SQLite Performance Benchmarking - Realistic Load Testing
Tests SQLite performance under realistic workload scenarios for the Whisper Transcriber application
"""

import os
import sys
import time
import threading
import random
import json
import uuid
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Tuple

# Add the project root to the path
sys.path.insert(0, '/home/buymeagoat/dev/whisper-transcriber')

from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.orm_bootstrap import Base, SessionLocal
from api.models import Job, User, TranscriptMetadata, AuditLog, JobStatusEnum
from api.settings import settings
from api.utils.logger import get_system_logger

logger = get_system_logger("db_benchmark")


class RealisticWorkloadBenchmark:
    """Comprehensive SQLite benchmarking with realistic workloads"""
    
    def __init__(self):
        self.results = {}
        self.test_data = {
            "users": [],
            "jobs": [],
            "metadata": []
        }
        
    def setup_test_data(self, num_users: int = 20, num_jobs: int = 100):
        """Create test data that mimics real application usage"""
        logger.info(f"Setting up test data: {num_users} users, {num_jobs} jobs")
        
        with SessionLocal() as db:
            # Clear existing test data
            db.query(AuditLog).filter(AuditLog.username.like('test_%')).delete()
            db.query(TranscriptMetadata).filter(TranscriptMetadata.job_id.like('test_%')).delete()
            db.query(Job).filter(Job.id.like('test_%')).delete()
            db.query(User).filter(User.username.like('test_%')).delete()
            db.commit()
            
            # Create test users
            for i in range(num_users):
                user = User(
                    username=f"test_user_{i:03d}",
                    hashed_password=f"hash_{i}",
                    role="admin" if i < 2 else "user",
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90))
                )
                db.add(user)
                self.test_data["users"].append(user)
            
            db.flush()  # Get user IDs
            
            # Create test jobs with realistic distribution
            statuses = [
                (JobStatusEnum.COMPLETED, 0.6),  # 60% completed
                (JobStatusEnum.FAILED, 0.15),    # 15% failed
                (JobStatusEnum.PROCESSING, 0.1), # 10% processing
                (JobStatusEnum.QUEUED, 0.15)     # 15% queued
            ]
            
            models = ["tiny", "small", "medium", "large"]
            
            for i in range(num_jobs):
                user = random.choice(self.test_data["users"])
                
                # Choose status based on distribution
                rand = random.random()
                cumulative = 0
                chosen_status = JobStatusEnum.QUEUED
                
                for status, probability in statuses:
                    cumulative += probability
                    if rand <= cumulative:
                        chosen_status = status
                        break
                
                created_at = datetime.utcnow() - timedelta(hours=random.randint(0, 72))
                
                job = Job(
                    id=f"test_job_{i:04d}",
                    original_filename=f"audio_{i:04d}.mp3",
                    saved_filename=f"saved_{i:04d}.wav",
                    model=random.choice(models),
                    status=chosen_status,
                    created_at=created_at,
                    updated_at=created_at + timedelta(minutes=random.randint(0, 10))
                )
                
                if chosen_status in [JobStatusEnum.PROCESSING, JobStatusEnum.COMPLETED, JobStatusEnum.FAILED]:
                    job.started_at = created_at + timedelta(minutes=random.randint(1, 30))
                
                if chosen_status in [JobStatusEnum.COMPLETED, JobStatusEnum.FAILED]:
                    job.finished_at = job.started_at + timedelta(minutes=random.randint(1, 60))
                
                db.add(job)
                self.test_data["jobs"].append(job)
            
            db.commit()
            logger.info("Test data creation completed")
    
    def simulate_user_session(self, user_id: int, session_duration_minutes: int = 10) -> Dict[str, Any]:
        """Simulate a realistic user session with multiple operations"""
        session_results = {
            "user_id": user_id,
            "operations": [],
            "total_time": 0,
            "successful_ops": 0,
            "failed_ops": 0,
            "errors": []
        }
        
        session_start = time.time()
        end_time = session_start + (session_duration_minutes * 60)
        
        # Typical user workflow operations
        operations = [
            ("login", self._simulate_login, 0.1),
            ("list_jobs", self._simulate_job_listing, 0.3),
            ("view_job", self._simulate_job_view, 0.2),
            ("upload_job", self._simulate_job_creation, 0.15),
            ("dashboard", self._simulate_dashboard_view, 0.2),
            ("admin_stats", self._simulate_admin_stats, 0.05)  # Admin users only
        ]
        
        while time.time() < end_time:
            # Choose operation based on weights
            operation_name, operation_func, weight = random.choices(
                operations, 
                weights=[op[2] for op in operations]
            )[0]
            
            op_start = time.time()
            
            try:
                result = operation_func(user_id)
                op_time = (time.time() - op_start) * 1000
                
                session_results["operations"].append({
                    "operation": operation_name,
                    "time_ms": op_time,
                    "success": True,
                    "result_size": len(str(result)) if result else 0
                })
                session_results["successful_ops"] += 1
                
            except Exception as e:
                op_time = (time.time() - op_start) * 1000
                session_results["operations"].append({
                    "operation": operation_name,
                    "time_ms": op_time,
                    "success": False,
                    "error": str(e)
                })
                session_results["failed_ops"] += 1
                session_results["errors"].append(f"{operation_name}: {str(e)}")
            
            # Random delay between operations (0.1-2 seconds)
            time.sleep(random.uniform(0.1, 2.0))
        
        session_results["total_time"] = time.time() - session_start
        return session_results
    
    def _simulate_login(self, user_id: int):
        """Simulate user login operations"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                # Simulate audit log entry
                audit = AuditLog(
                    timestamp=datetime.utcnow(),
                    event_type="login",
                    severity="low",
                    user_id=user_id,
                    username=user.username,
                    client_ip=f"192.168.1.{random.randint(1, 254)}",
                    endpoint="/login",
                    method="POST",
                    status_code=200
                )
                db.add(audit)
                db.commit()
            return user
    
    def _simulate_job_listing(self, user_id: int):
        """Simulate job listing with pagination"""
        with SessionLocal() as db:
            page_size = random.randint(10, 50)
            jobs = db.query(Job).limit(page_size).all()
            
            # Simulate accessing related data (potential N+1 scenario)
            for job in jobs[:5]:  # Only check first 5 to avoid excessive queries
                metadata = db.query(TranscriptMetadata).filter(
                    TranscriptMetadata.job_id == job.id
                ).first()
            
            return jobs
    
    def _simulate_job_view(self, user_id: int):
        """Simulate viewing a specific job with metadata"""
        with SessionLocal() as db:
            job = db.query(Job).filter(Job.id.like('test_%')).first()
            if job:
                metadata = db.query(TranscriptMetadata).filter(
                    TranscriptMetadata.job_id == job.id
                ).first()
                return {"job": job, "metadata": metadata}
            return None
    
    def _simulate_job_creation(self, user_id: int):
        """Simulate creating a new job"""
        with SessionLocal() as db:
            job_id = f"test_sim_{uuid.uuid4().hex[:8]}"
            
            job = Job(
                id=job_id,
                original_filename=f"uploaded_{int(time.time())}.mp3",
                saved_filename=f"saved_{int(time.time())}.wav",
                model=random.choice(["tiny", "small", "medium"]),
                status=JobStatusEnum.QUEUED,
                created_at=datetime.utcnow()
            )
            
            db.add(job)
            db.commit()
            
            # Simulate audit log
            audit = AuditLog(
                timestamp=datetime.utcnow(),
                event_type="job_created",
                severity="low",
                user_id=user_id,
                client_ip=f"192.168.1.{random.randint(1, 254)}",
                endpoint="/jobs",
                method="POST",
                status_code=201,
                resource_id=job_id
            )
            db.add(audit)
            db.commit()
            
            return job
    
    def _simulate_dashboard_view(self, user_id: int):
        """Simulate dashboard data aggregation"""
        with SessionLocal() as db:
            # Job statistics
            total_jobs = db.query(Job).filter(Job.id.like('test_%')).count()
            completed_jobs = db.query(Job).filter(
                Job.id.like('test_%'),
                Job.status == JobStatusEnum.COMPLETED
            ).count()
            
            # Recent activity
            recent_jobs = db.query(Job).filter(
                Job.id.like('test_%')
            ).order_by(Job.created_at.desc()).limit(10).all()
            
            return {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "recent_jobs": len(recent_jobs)
            }
    
    def _simulate_admin_stats(self, user_id: int):
        """Simulate admin statistics queries"""
        with SessionLocal() as db:
            # Complex aggregation queries
            stats = db.query(
                func.count(Job.id).label('total'),
                func.avg(func.case([(Job.finished_at.isnot(None), 
                    func.extract('epoch', Job.finished_at - Job.started_at))], else_=None)).label('avg_duration')
            ).filter(Job.id.like('test_%')).first()
            
            # User activity
            user_activity = db.query(
                func.count(AuditLog.id).label('events'),
                func.count(func.distinct(AuditLog.user_id)).label('active_users')
            ).filter(AuditLog.timestamp >= datetime.utcnow() - timedelta(hours=24)).first()
            
            return {
                "job_stats": stats,
                "user_activity": user_activity
            }
    
    def run_concurrent_user_sessions(self, num_concurrent_users: int = 10, 
                                   session_duration_minutes: int = 5) -> Dict[str, Any]:
        """Run multiple concurrent user sessions"""
        logger.info(f"Running {num_concurrent_users} concurrent user sessions for {session_duration_minutes} minutes each")
        
        benchmark_start = time.time()
        results = {
            "concurrent_users": num_concurrent_users,
            "session_duration_minutes": session_duration_minutes,
            "sessions": [],
            "summary": {},
            "errors": []
        }
        
        # Use ThreadPoolExecutor for controlled concurrency
        with ThreadPoolExecutor(max_workers=num_concurrent_users) as executor:
            # Submit user sessions
            future_to_user = {
                executor.submit(self.simulate_user_session, user_id % len(self.test_data["users"]) + 1, session_duration_minutes): user_id
                for user_id in range(num_concurrent_users)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_user):
                user_id = future_to_user[future]
                try:
                    session_result = future.result()
                    results["sessions"].append(session_result)
                except Exception as e:
                    error_msg = f"User {user_id} session failed: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
        
        total_benchmark_time = time.time() - benchmark_start
        
        # Calculate summary statistics
        all_operation_times = []
        total_operations = 0
        total_successful = 0
        total_failed = 0
        operation_type_stats = {}
        
        for session in results["sessions"]:
            total_operations += len(session["operations"])
            total_successful += session["successful_ops"]
            total_failed += session["failed_ops"]
            
            for op in session["operations"]:
                all_operation_times.append(op["time_ms"])
                
                op_type = op["operation"]
                if op_type not in operation_type_stats:
                    operation_type_stats[op_type] = {"times": [], "successes": 0, "failures": 0}
                
                operation_type_stats[op_type]["times"].append(op["time_ms"])
                if op["success"]:
                    operation_type_stats[op_type]["successes"] += 1
                else:
                    operation_type_stats[op_type]["failures"] += 1
        
        if all_operation_times:
            import statistics
            results["summary"] = {
                "total_benchmark_time": total_benchmark_time,
                "total_operations": total_operations,
                "successful_operations": total_successful,
                "failed_operations": total_failed,
                "success_rate": (total_successful / total_operations * 100) if total_operations > 0 else 0,
                "operations_per_second": total_operations / total_benchmark_time if total_benchmark_time > 0 else 0,
                "avg_operation_time_ms": statistics.mean(all_operation_times),
                "median_operation_time_ms": statistics.median(all_operation_times),
                "min_operation_time_ms": min(all_operation_times),
                "max_operation_time_ms": max(all_operation_times),
                "std_dev_operation_time": statistics.stdev(all_operation_times),
                "operation_type_breakdown": {}
            }
            
            # Per-operation type statistics
            for op_type, stats in operation_type_stats.items():
                if stats["times"]:
                    results["summary"]["operation_type_breakdown"][op_type] = {
                        "avg_time_ms": statistics.mean(stats["times"]),
                        "successes": stats["successes"],
                        "failures": stats["failures"],
                        "success_rate": (stats["successes"] / (stats["successes"] + stats["failures"]) * 100)
                    }
        
        return results
    
    def test_database_locking_scenarios(self) -> Dict[str, Any]:
        """Test specific SQLite locking scenarios"""
        logger.info("Testing SQLite locking scenarios...")
        
        lock_test_results = {
            "read_while_write": {},
            "multiple_writes": {},
            "long_transaction": {},
            "transaction_rollback": {}
        }
        
        # Test 1: Read operations during write operations
        def write_operation():
            try:
                with SessionLocal() as db:
                    for i in range(10):
                        job = Job(
                            id=f"lock_test_write_{i}_{int(time.time())}",
                            original_filename=f"test_{i}.mp3",
                            saved_filename=f"test_{i}.wav",
                            model="tiny",
                            status=JobStatusEnum.QUEUED
                        )
                        db.add(job)
                        time.sleep(0.1)  # Simulate processing time
                    db.commit()
                return True
            except Exception as e:
                return str(e)
        
        def read_operation():
            try:
                with SessionLocal() as db:
                    count = db.query(Job).count()
                    return count
            except Exception as e:
                return str(e)
        
        # Test concurrent reads during writes
        write_start = time.time()
        write_thread = threading.Thread(target=write_operation)
        write_thread.start()
        
        read_results = []
        read_errors = []
        
        while write_thread.is_alive():
            read_start = time.time()
            result = read_operation()
            read_time = (time.time() - read_start) * 1000
            
            if isinstance(result, str):  # Error
                read_errors.append(result)
            else:
                read_results.append(read_time)
            
            time.sleep(0.05)
        
        write_thread.join()
        write_time = (time.time() - write_start) * 1000
        
        lock_test_results["read_while_write"] = {
            "write_time_ms": write_time,
            "successful_reads": len(read_results),
            "failed_reads": len(read_errors),
            "avg_read_time_ms": sum(read_results) / len(read_results) if read_results else 0,
            "read_errors": read_errors[:5]  # First 5 errors
        }
        
        # Test 2: Multiple simultaneous write attempts
        def concurrent_write(thread_id):
            try:
                with SessionLocal() as db:
                    job = Job(
                        id=f"concurrent_write_{thread_id}_{int(time.time())}",
                        original_filename=f"concurrent_{thread_id}.mp3",
                        saved_filename=f"concurrent_{thread_id}.wav",
                        model="tiny",
                        status=JobStatusEnum.QUEUED
                    )
                    db.add(job)
                    db.commit()
                return True, None
            except Exception as e:
                return False, str(e)
        
        write_threads = []
        write_results = []
        
        start_time = time.time()
        for i in range(5):
            thread = threading.Thread(target=lambda tid=i: write_results.append(concurrent_write(tid)))
            write_threads.append(thread)
            thread.start()
        
        for thread in write_threads:
            thread.join()
        
        total_write_time = (time.time() - start_time) * 1000
        
        successful_writes = sum(1 for success, _ in write_results if success)
        failed_writes = sum(1 for success, _ in write_results if not success)
        write_errors = [error for success, error in write_results if not success]
        
        lock_test_results["multiple_writes"] = {
            "total_time_ms": total_write_time,
            "successful_writes": successful_writes,
            "failed_writes": failed_writes,
            "write_errors": write_errors[:3]  # First 3 errors
        }
        
        return lock_test_results
    
    def cleanup_test_data(self):
        """Clean up test data"""
        logger.info("Cleaning up test data...")
        
        try:
            with SessionLocal() as db:
                # Delete in correct order due to foreign keys
                db.query(AuditLog).filter(AuditLog.username.like('test_%')).delete()
                db.query(TranscriptMetadata).filter(TranscriptMetadata.job_id.like('test_%')).delete()
                db.query(Job).filter(Job.id.like('test_%')).delete()
                db.query(Job).filter(Job.id.like('lock_test_%')).delete()
                db.query(Job).filter(Job.id.like('concurrent_%')).delete()
                db.query(User).filter(User.username.like('test_%')).delete()
                db.commit()
                logger.info("Test data cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive SQLite performance benchmark"""
        logger.info("Starting comprehensive SQLite benchmark...")
        
        benchmark_results = {
            "benchmark_timestamp": datetime.utcnow().isoformat(),
            "database_config": {
                "type": "SQLite",
                "url": settings.database_url,
                "version": None
            },
            "test_scenarios": {}
        }
        
        try:
            # Get SQLite version
            with SessionLocal() as db:
                version = db.execute(text("SELECT sqlite_version()")).scalar()
                benchmark_results["database_config"]["version"] = version
        except Exception as e:
            benchmark_results["database_config"]["version_error"] = str(e)
        
        try:
            # Setup test data
            self.setup_test_data(15, 75)
            
            # Test 1: Light concurrent load (5 users)
            logger.info("Testing light concurrent load (5 users)...")
            benchmark_results["test_scenarios"]["light_load"] = self.run_concurrent_user_sessions(5, 3)
            
            # Test 2: Medium concurrent load (10 users)
            logger.info("Testing medium concurrent load (10 users)...")
            benchmark_results["test_scenarios"]["medium_load"] = self.run_concurrent_user_sessions(10, 3)
            
            # Test 3: Heavy concurrent load (15 users)
            logger.info("Testing heavy concurrent load (15 users)...")
            benchmark_results["test_scenarios"]["heavy_load"] = self.run_concurrent_user_sessions(15, 2)
            
            # Test 4: Database locking scenarios
            benchmark_results["test_scenarios"]["locking_tests"] = self.test_database_locking_scenarios()
            
        except Exception as e:
            benchmark_results["benchmark_error"] = str(e)
            logger.error(f"Benchmark failed: {e}")
        
        finally:
            # Always cleanup
            self.cleanup_test_data()
        
        return benchmark_results


def main():
    """Run SQLite performance benchmark"""
    print("SQLite Performance Benchmark - Realistic Load Testing")
    print("=" * 60)
    
    benchmark = RealisticWorkloadBenchmark()
    
    try:
        results = benchmark.run_comprehensive_benchmark()
        
        # Print summary
        print("\nBENCHMARK SUMMARY")
        print("-" * 30)
        
        for scenario_name, scenario_data in results.get("test_scenarios", {}).items():
            if scenario_name == "locking_tests":
                continue  # Skip locking tests in summary
                
            print(f"\n{scenario_name.upper()}:")
            summary = scenario_data.get("summary", {})
            
            if summary:
                print(f"  Operations/second: {summary.get('operations_per_second', 0):.1f}")
                print(f"  Success rate: {summary.get('success_rate', 0):.1f}%")
                print(f"  Avg operation time: {summary.get('avg_operation_time_ms', 0):.1f}ms")
                print(f"  Failed operations: {summary.get('failed_operations', 0)}")
        
        # Locking test summary
        locking_data = results.get("test_scenarios", {}).get("locking_tests", {})
        if locking_data:
            print(f"\nLOCKING TESTS:")
            read_while_write = locking_data.get("read_while_write", {})
            multiple_writes = locking_data.get("multiple_writes", {})
            
            print(f"  Read-while-write: {read_while_write.get('successful_reads', 0)} successful reads, {read_while_write.get('failed_reads', 0)} failed")
            print(f"  Concurrent writes: {multiple_writes.get('successful_writes', 0)}/{multiple_writes.get('successful_writes', 0) + multiple_writes.get('failed_writes', 0)} successful")
        
        # Save detailed results
        output_file = "/home/buymeagoat/dev/whisper-transcriber/temp/sqlite_benchmark_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nDetailed results saved to: {output_file}")
        
        # Performance assessment
        print("\nPERFORMANCE ASSESSMENT:")
        print("-" * 30)
        
        heavy_load = results.get("test_scenarios", {}).get("heavy_load", {}).get("summary", {})
        if heavy_load:
            ops_per_sec = heavy_load.get("operations_per_second", 0)
            success_rate = heavy_load.get("success_rate", 0)
            avg_time = heavy_load.get("avg_operation_time_ms", 0)
            
            if ops_per_sec < 50:
                print("❌ LOW THROUGHPUT: SQLite struggling with concurrent load")
            elif ops_per_sec < 100:
                print("⚠️  MODERATE THROUGHPUT: SQLite managing but showing strain")
            else:
                print("✅ GOOD THROUGHPUT: SQLite handling load well")
            
            if success_rate < 95:
                print("❌ HIGH ERROR RATE: Significant concurrent operation failures")
            elif success_rate < 99:
                print("⚠️  MODERATE ERROR RATE: Some concurrent operation issues")
            else:
                print("✅ LOW ERROR RATE: Concurrent operations mostly successful")
            
            if avg_time > 200:
                print("❌ SLOW OPERATIONS: Average operation time concerning")
            elif avg_time > 100:
                print("⚠️  MODERATE SPEED: Operation times acceptable but could improve")
            else:
                print("✅ FAST OPERATIONS: Good operation response times")
        
        return results
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        print(f"❌ Benchmark failed: {e}")
        return None


if __name__ == "__main__":
    main()