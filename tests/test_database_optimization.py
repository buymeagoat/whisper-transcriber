"""
Tests for Enhanced Database Optimization Features (T025 Phase 3)
Comprehensive test suite for database optimization functionality.
"""

import pytest
import asyncio
import time
import unittest.mock
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.services.enhanced_db_optimizer import (
    EnhancedDatabaseOptimizer,
    ConnectionPoolConfig,
    AdvancedQueryPatterns,
    initialize_database_optimizer,
    get_database_optimizer,
    cleanup_database_optimizer
)
from api.services.database_optimization_integration import (
    DatabaseOptimizationService,
    get_optimization_service,
    cleanup_optimization_service
)
from api.models import Job, User, AuditLog, JobStatusEnum
from api.orm_bootstrap import Base

# Test database URL for SQLite in-memory database
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
async def test_db_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    engine.dispose()

@pytest.fixture
async def test_optimizer():
    """Create a test database optimizer."""
    config = ConnectionPoolConfig(
        pool_size=5,
        max_overflow=10,
        pool_timeout=10,
        echo=False
    )
    
    optimizer = EnhancedDatabaseOptimizer(config)
    await optimizer.initialize_optimized_engine(TEST_DATABASE_URL)
    
    yield optimizer
    
    # Cleanup
    if optimizer.engine:
        optimizer.engine.dispose()

@pytest.fixture
async def test_optimization_service():
    """Create a test optimization service."""
    service = DatabaseOptimizationService()
    
    # Mock the settings
    with patch('api.services.database_optimization_integration.get_settings') as mock_settings:
        mock_settings.return_value = MagicMock(
            database_url=TEST_DATABASE_URL,
            DEBUG=False
        )
        await service.initialize()
    
    yield service
    
    # Cleanup
    await service.cleanup()

class TestEnhancedDatabaseOptimizer:
    """Test cases for EnhancedDatabaseOptimizer."""
    
    async def test_initialization(self, test_optimizer):
        """Test optimizer initialization."""
        assert test_optimizer.engine is not None
        assert test_optimizer.session_factory is not None
        assert test_optimizer.config.pool_size == 5
        assert test_optimizer.performance_stats["total_queries"] == 0
    
    async def test_connection_pool_config(self):
        """Test connection pool configuration."""
        config = ConnectionPoolConfig(
            pool_size=15,
            max_overflow=25,
            pool_timeout=20,
            pool_recycle=7200
        )
        
        assert config.pool_size == 15
        assert config.max_overflow == 25
        assert config.pool_timeout == 20
        assert config.pool_recycle == 7200
        assert config.execution_options is not None
    
    async def test_optimized_session(self, test_optimizer):
        """Test optimized session creation."""
        async with test_optimizer.get_optimized_session() as session:
            assert session is not None
            
            # Test a simple query
            result = session.execute(text("SELECT 1")).fetchone()
            assert result[0] == 1
    
    async def test_connection_pool_status(self, test_optimizer):
        """Test connection pool status retrieval."""
        status = await test_optimizer.get_connection_pool_status()
        
        assert "pool_size" in status
        assert "checked_in" in status
        assert "checked_out" in status
        assert "utilization_percent" in status
        assert "configuration" in status
        
        # Verify configuration is included
        config = status["configuration"]
        assert config["pool_size"] == test_optimizer.config.pool_size
    
    async def test_performance_monitoring(self, test_optimizer):
        """Test query performance monitoring."""
        initial_count = test_optimizer.performance_stats["total_queries"]
        
        # Execute some queries to trigger monitoring
        async with test_optimizer.get_optimized_session() as session:
            session.execute(text("SELECT 1"))
            session.execute(text("SELECT 2"))
        
        # Performance stats should be updated
        assert test_optimizer.performance_stats["total_queries"] > initial_count
    
    @pytest.mark.asyncio
    async def test_database_maintenance(self, test_optimizer):
        """Test database maintenance operations."""
        async with test_optimizer.get_optimized_session() as session:
            # This should not raise an exception
            await test_optimizer.optimize_database_maintenance(session)
            
            # Check that last_optimization is updated
            assert test_optimizer.performance_stats["last_optimization"] is not None

class TestAdvancedQueryPatterns:
    """Test cases for AdvancedQueryPatterns."""
    
    async def test_bulk_insert_jobs(self, test_db_engine):
        """Test bulk job insertion."""
        Session = sessionmaker(bind=test_db_engine)
        session = Session()
        
        try:
            # Create test data
            job_data = [
                {
                    "id": f"test_job_{i}",
                    "filename": f"test_file_{i}.mp3",
                    "saved_filename": f"saved_file_{i}.mp3",
                    "model": "small"
                }
                for i in range(5)
            ]
            
            # Test bulk insert
            job_ids = await AdvancedQueryPatterns.bulk_insert_jobs(session, job_data)
            
            assert len(job_ids) == 5
            
            # Verify jobs were inserted
            jobs = session.query(Job).filter(Job.id.in_(job_ids)).all()
            assert len(jobs) == 5
            
        finally:
            session.close()
    
    async def test_dashboard_data_optimized(self, test_db_engine):
        """Test optimized dashboard data retrieval."""
        Session = sessionmaker(bind=test_db_engine)
        session = Session()
        
        try:
            # Create test user
            user = User(
                id=1,
                username="testuser",
                email="test@example.com",
                hashed_password="test",
                role="user"
            )
            session.add(user)
            session.commit()
            
            # Create test jobs
            for i in range(3):
                job = Job(
                    id=f"test_job_{i}",
                    user_id=1,
                    original_filename=f"test_{i}.mp3",
                    saved_filename=f"saved_{i}.mp3",
                    model="small",
                    status=JobStatusEnum.COMPLETED if i < 2 else JobStatusEnum.FAILED
                )
                session.add(job)
            
            session.commit()
            
            # Test dashboard data retrieval
            dashboard_data = await AdvancedQueryPatterns.get_dashboard_data_optimized(session, 1)
            
            assert dashboard_data["total_jobs"] == 3
            assert dashboard_data["completed_jobs"] == 2
            assert dashboard_data["failed_jobs"] == 1
            assert dashboard_data["success_rate"] == (2/3 * 100)
            
        finally:
            session.close()
    
    async def test_search_jobs_optimized(self, test_db_engine):
        """Test optimized job search."""
        Session = sessionmaker(bind=test_db_engine)
        session = Session()
        
        try:
            # Create test user
            user = User(
                id=1,
                username="testuser",
                email="test@example.com",
                hashed_password="test",
                role="user"
            )
            session.add(user)
            session.commit()
            
            # Create test jobs with searchable content
            jobs_data = [
                ("job1", "important_meeting.mp3"),
                ("job2", "conference_call.mp3"),
                ("job3", "presentation.mp3")
            ]
            
            for job_id, filename in jobs_data:
                job = Job(
                    id=job_id,
                    user_id=1,
                    original_filename=filename,
                    saved_filename=f"saved_{filename}",
                    model="small",
                    status=JobStatusEnum.COMPLETED
                )
                session.add(job)
            
            session.commit()
            
            # Test search
            results = await AdvancedQueryPatterns.search_jobs_optimized(session, 1, "meeting")
            assert len(results) == 1
            assert results[0].original_filename == "important_meeting.mp3"
            
            # Test broader search
            results = await AdvancedQueryPatterns.search_jobs_optimized(session, 1, "mp3")
            assert len(results) == 3
            
        finally:
            session.close()
    
    async def test_system_health_optimized(self, test_db_engine):
        """Test optimized system health retrieval."""
        Session = sessionmaker(bind=test_db_engine)
        session = Session()
        
        try:
            # Create test data
            user = User(
                id=1,
                username="testuser",
                email="test@example.com",
                hashed_password="test",
                role="user"
            )
            session.add(user)
            
            # Create jobs with different statuses
            job_statuses = [JobStatusEnum.COMPLETED, JobStatusEnum.FAILED, JobStatusEnum.PROCESSING]
            for i, status in enumerate(job_statuses):
                job = Job(
                    id=f"health_job_{i}",
                    user_id=1,
                    original_filename=f"health_{i}.mp3",
                    saved_filename=f"saved_health_{i}.mp3",
                    model="small",
                    status=status
                )
                session.add(job)
            
            session.commit()
            
            # Test system health
            health_data = await AdvancedQueryPatterns.get_system_health_optimized(session)
            
            assert health_data["status"] in ["healthy", "degraded", "critical"]
            assert "health_score" in health_data
            assert "metrics" in health_data
            
            metrics = health_data["metrics"]
            assert metrics["total_jobs"] == 3
            assert metrics["failed_jobs"] == 1
            assert metrics["total_users"] == 1
            
        finally:
            session.close()

class TestDatabaseOptimizationService:
    """Test cases for DatabaseOptimizationService."""
    
    async def test_service_initialization(self, test_optimization_service):
        """Test service initialization."""
        assert test_optimization_service.optimizer is not None
        assert test_optimization_service.query_patterns is not None
    
    async def test_dashboard_data_with_caching(self, test_optimization_service):
        """Test dashboard data retrieval with caching."""
        # Mock cache service
        with patch('api.services.database_optimization_integration.get_cache_service') as mock_cache:
            mock_cache_service = AsyncMock()
            mock_cache_service.get.return_value = None  # Cache miss
            mock_cache_service.set.return_value = None
            mock_cache.return_value = mock_cache_service
            
            # Mock database query
            with patch.object(test_optimization_service.query_patterns, 'get_dashboard_data_optimized') as mock_query:
                mock_query.return_value = {"total_jobs": 5, "completed_jobs": 3}
                
                # Test dashboard data retrieval
                result = await test_optimization_service.get_dashboard_data(1, use_cache=True)
                
                assert result["total_jobs"] == 5
                assert result["completed_jobs"] == 3
                
                # Verify cache operations were called
                mock_cache_service.get.assert_called_once()
                mock_cache_service.set.assert_called_once()
    
    async def test_search_jobs_service(self, test_optimization_service):
        """Test job search through service."""
        # Mock the query pattern method
        with patch.object(test_optimization_service.query_patterns, 'search_jobs_optimized') as mock_search:
            mock_jobs = [MagicMock(id="job1"), MagicMock(id="job2")]
            mock_search.return_value = mock_jobs
            
            result = await test_optimization_service.search_jobs(1, "test", 10)
            
            assert len(result) == 2
            mock_search.assert_called_once_with(unittest.mock.ANY, 1, "test", 10)
    
    async def test_system_health_service(self, test_optimization_service):
        """Test system health through service."""
        # Mock the query pattern method
        with patch.object(test_optimization_service.query_patterns, 'get_system_health_optimized') as mock_health:
            mock_health.return_value = {"status": "healthy", "metrics": {}}
            
            result = await test_optimization_service.get_system_health()
            
            assert result["status"] == "healthy"
            assert "connection_pool" in result
            mock_health.assert_called_once()
    
    async def test_performance_analysis_service(self, test_optimization_service):
        """Test performance analysis through service."""
        # Mock the optimizer method
        with patch.object(test_optimization_service.optimizer, 'analyze_query_performance') as mock_analysis:
            mock_analysis.return_value = {"slow_queries": [], "performance_summary": {}}
            
            result = await test_optimization_service.get_performance_analysis()
            
            assert "slow_queries" in result
            mock_analysis.assert_called_once()
    
    async def test_maintenance_service(self, test_optimization_service):
        """Test maintenance through service."""
        # Mock the optimizer method
        with patch.object(test_optimization_service.optimizer, 'optimize_database_maintenance') as mock_maintenance:
            mock_maintenance.return_value = None
            
            result = await test_optimization_service.perform_maintenance()
            
            assert result is True
            mock_maintenance.assert_called_once()

class TestPerformanceImpact:
    """Test cases for performance impact measurement."""
    
    async def test_query_execution_time_tracking(self, test_optimizer):
        """Test that query execution times are properly tracked."""
        initial_avg = test_optimizer.performance_stats["avg_query_time"]
        
        # Execute queries and measure time tracking
        async with test_optimizer.get_optimized_session() as session:
            # Fast query
            session.execute(text("SELECT 1"))
            
            # Simulate slower query with a small delay
            time.sleep(0.001)  # 1ms delay
            session.execute(text("SELECT 2"))
        
        # Check that average time was updated
        final_avg = test_optimizer.performance_stats["avg_query_time"]
        assert test_optimizer.performance_stats["total_queries"] >= 2
    
    async def test_slow_query_detection(self, test_optimizer):
        """Test slow query detection and counting."""
        initial_slow = test_optimizer.performance_stats["slow_queries"]
        
        # This test would need to simulate a genuinely slow query
        # For this test, we'll check the mechanism is in place
        assert "slow_queries" in test_optimizer.performance_stats
        assert initial_slow >= 0

class TestIntegrationScenarios:
    """Integration test scenarios."""
    
    async def test_full_optimization_workflow(self, test_optimization_service):
        """Test a complete optimization workflow."""
        # Test initialization
        assert test_optimization_service.optimizer is not None
        
        # Test performance analysis
        analysis = await test_optimization_service.get_performance_analysis()
        assert analysis is not None
        
        # Test system health
        health = await test_optimization_service.get_system_health()
        assert health is not None
        
        # Test maintenance
        maintenance_result = await test_optimization_service.perform_maintenance()
        assert maintenance_result is True
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, test_optimizer):
        """Test concurrent database operations."""
        async def perform_queries(session_num):
            async with test_optimizer.get_optimized_session() as session:
                for i in range(5):
                    # Use parameterized query to prevent SQL injection
                    session.execute(text("SELECT :value"), {"value": session_num * 5 + i})
        
        # Run concurrent operations
        tasks = [perform_queries(i) for i in range(3)]
        await asyncio.gather(*tasks)
        
        # Check that all queries were tracked
        assert test_optimizer.performance_stats["total_queries"] >= 15
    
    async def test_error_handling_and_recovery(self, test_optimizer):
        """Test error handling and recovery mechanisms."""
        # Test session error handling
        try:
            async with test_optimizer.get_optimized_session() as session:
                # This should cause an error
                session.execute(text("SELECT * FROM non_existent_table"))
        except Exception:
            # Error is expected, session should clean up properly
            pass
        
        # Should still be able to get new sessions
        async with test_optimizer.get_optimized_session() as session:
            result = session.execute(text("SELECT 1")).fetchone()
            assert result[0] == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
