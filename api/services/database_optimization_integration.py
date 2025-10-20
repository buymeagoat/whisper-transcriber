"""
Database Optimization Integration Module
Integrates enhanced database optimization with existing FastAPI application.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

from api.orm_bootstrap import get_db, SessionLocal
from api.services.enhanced_db_optimizer import (
    EnhancedDatabaseOptimizer,
    ConnectionPoolConfig,
    AdvancedQueryPatterns,
    initialize_database_optimizer,
    get_database_optimizer,
    cleanup_database_optimizer
)
from api.services.redis_cache import get_cache_service
from api.utils.logger import get_system_logger
from api.settings import settings

logger = get_system_logger("db_integration")

class DatabaseOptimizationService:
    """Service to manage database optimization features."""
    
    def __init__(self):
        self.optimizer: Optional[EnhancedDatabaseOptimizer] = None
        self.query_patterns = AdvancedQueryPatterns()
        self.performance_cache = {}
        
    async def initialize(self):
        """Initialize database optimization service."""
        try:
            # Configure connection pool based on environment
            config = ConnectionPoolConfig(
                pool_size=settings.DB_POOL_SIZE if hasattr(settings, 'DB_POOL_SIZE') else 10,
                max_overflow=settings.DB_MAX_OVERFLOW if hasattr(settings, 'DB_MAX_OVERFLOW') else 20,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=settings.debug if hasattr(settings, 'debug') else False
            )
            
            # Initialize optimizer
            await initialize_database_optimizer(settings.db_url, config)
            self.optimizer = await get_database_optimizer()
            
            logger.info("Database optimization service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize database optimization service: {e}")
            raise
    
    async def get_optimized_session(self):
        """Get an optimized database session."""
        if not self.optimizer:
            # Fallback to regular session
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()
        else:
            async with self.optimizer.get_optimized_session() as session:
                yield session
    
    async def get_dashboard_data(self, user_id: int, use_cache: bool = True) -> Dict[str, Any]:
        """Get dashboard data with optimization and caching."""
        cache_key = f"dashboard_data_{user_id}"
        
        # Try cache first if enabled
        if use_cache:
            cache_service = get_cache_service()
            if cache_service:
                cached_data = await cache_service.get(cache_key)
                if cached_data:
                    logger.debug(f"Dashboard data cache hit for user {user_id}")
                    return cached_data
        
        # Get data using optimized query
        try:
            if self.optimizer:
                async with self.optimizer.get_optimized_session() as session:
                    data = await self.query_patterns.get_dashboard_data_optimized(session, user_id)
            else:
                # Fallback to regular session
                with SessionLocal() as session:
                    data = await self.query_patterns.get_dashboard_data_optimized(session, user_id)
            
            # Cache the result for 5 minutes
            if use_cache:
                cache_service = get_cache_service()
                if cache_service:
                    await cache_service.set(cache_key, data, 300)  # 5 minutes
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch dashboard data")
    
    async def search_jobs(self, user_id: int, search_term: str, limit: int = 20) -> list:
        """Search jobs with optimization."""
        try:
            if self.optimizer:
                async with self.optimizer.get_optimized_session() as session:
                    jobs = await self.query_patterns.search_jobs_optimized(
                        session, user_id, search_term, limit
                    )
            else:
                # Fallback to regular session
                with SessionLocal() as session:
                    jobs = await self.query_patterns.search_jobs_optimized(
                        session, user_id, search_term, limit
                    )
            
            return jobs
            
        except Exception as e:
            logger.error(f"Job search failed for user {user_id}, term '{search_term}': {e}")
            raise HTTPException(status_code=500, detail="Search failed")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health with optimization."""
        try:
            if self.optimizer:
                async with self.optimizer.get_optimized_session() as session:
                    health_data = await self.query_patterns.get_system_health_optimized(session)
            else:
                # Fallback to regular session
                with SessionLocal() as session:
                    health_data = await self.query_patterns.get_system_health_optimized(session)
            
            # Add connection pool status if available
            if self.optimizer:
                pool_status = await self.optimizer.get_connection_pool_status()
                health_data["connection_pool"] = pool_status
            
            return health_data
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_performance_analysis(self) -> Dict[str, Any]:
        """Get database performance analysis."""
        try:
            if not self.optimizer:
                return {"status": "optimizer_not_available"}
            
            async with self.optimizer.get_optimized_session() as session:
                analysis = await self.optimizer.analyze_query_performance(session)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {"error": str(e)}
    
    async def perform_maintenance(self):
        """Perform database maintenance operations."""
        try:
            if not self.optimizer:
                logger.warning("Database optimizer not available for maintenance")
                return False
            
            async with self.optimizer.get_optimized_session() as session:
                await self.optimizer.optimize_database_maintenance(session)
            
            logger.info("Database maintenance completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database maintenance failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup optimization service."""
        await cleanup_database_optimizer()
        self.optimizer = None
        logger.info("Database optimization service cleaned up")

# Global service instance
_optimization_service: Optional[DatabaseOptimizationService] = None

async def get_optimization_service() -> DatabaseOptimizationService:
    """Get the global database optimization service."""
    global _optimization_service
    
    if _optimization_service is None:
        _optimization_service = DatabaseOptimizationService()
        await _optimization_service.initialize()
    
    return _optimization_service

async def cleanup_optimization_service():
    """Cleanup the optimization service."""
    global _optimization_service
    
    if _optimization_service:
        await _optimization_service.cleanup()
        _optimization_service = None

@asynccontextmanager
async def database_optimization_lifespan(app: FastAPI):
    """FastAPI lifespan context manager for database optimization."""
    try:
        # Initialize on startup
        optimization_service = await get_optimization_service()
        logger.info("Database optimization initialized during app startup")
        
        yield
        
    finally:
        # Cleanup on shutdown
        await cleanup_optimization_service()
        logger.info("Database optimization cleaned up during app shutdown")

# Enhanced dependency injection for optimized database sessions
async def get_optimized_db() -> Session:
    """Dependency to get an optimized database session."""
    try:
        optimization_service = await get_optimization_service()
        
        if optimization_service.optimizer:
            async with optimization_service.optimizer.get_optimized_session() as session:
                yield session
        else:
            # Fallback to regular session
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()
                
    except Exception as e:
        logger.error(f"Failed to get optimized database session: {e}")
        # Fallback to regular session
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

# Performance monitoring utilities
async def monitor_query_performance(endpoint: str, query_type: str):
    """Decorator to monitor query performance for specific endpoints."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Log performance metrics
                optimization_service = await get_optimization_service()
                if optimization_service.optimizer:
                    optimization_service.optimizer.performance_stats["total_queries"] += 1
                    
                    if execution_time > 100:  # Slow query threshold
                        optimization_service.optimizer.performance_stats["slow_queries"] += 1
                        logger.warning(f"Slow query in {endpoint}: {execution_time:.2f}ms")
                
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"Query failed in {endpoint}: {e} (took {execution_time:.2f}ms)")
                raise
                
        return wrapper
    return decorator
