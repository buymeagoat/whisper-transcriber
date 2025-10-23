"""
Enhanced Database Query Optimization for T025 Phase 3
Advanced query optimization patterns and connection pool management.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from sqlalchemy import create_engine, event, text, Index
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.orm import joinedload, selectinload, contains_eager

from api.models import Job, User, TranscriptMetadata, AuditLog, JobStatusEnum
from api.orm_bootstrap import SessionLocal
from api.utils.logger import get_system_logger

logger = get_system_logger("db_optimization")

@dataclass
class ConnectionPoolConfig:
    """Advanced connection pool configuration."""
    pool_size: int = 20  # Base number of connections
    max_overflow: int = 30  # Additional connections when needed
    pool_timeout: int = 30  # Seconds to wait for connection
    pool_recycle: int = 3600  # Recycle connections after 1 hour
    pool_pre_ping: bool = True  # Validate connections before use
    echo: bool = False  # SQL logging
    
    # Advanced pool settings
    pool_reset_on_return: str = "commit"  # Reset strategy
    pool_invalidation_on_disconnect: bool = True
    
    # Performance tuning
    execution_options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.execution_options is None:
            self.execution_options = {
                "autocommit": False,
                "isolation_level": "READ_COMMITTED",
                "compiled_cache": {},  # Enable query compilation caching
            }

class EnhancedDatabaseOptimizer:
    """Advanced database optimization with connection pooling and query analysis."""
    
    def __init__(self, config: ConnectionPoolConfig = None):
        self.config = config or ConnectionPoolConfig()
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker] = None
        self.query_cache: Dict[str, Any] = {}
        self.performance_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "cache_hits": 0,
            "connection_pool_stats": {},
            "avg_query_time": 0.0,
            "last_optimization": None
        }
        
    async def initialize_optimized_engine(self, database_url: str):
        """Initialize database engine with advanced optimization settings."""
        try:
            # Create optimized engine with connection pooling
            self.engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=self.config.pool_pre_ping,
                pool_reset_on_return=self.config.pool_reset_on_return,
                echo=self.config.echo,
                execution_options=self.config.execution_options,
                
                # SQLite-specific optimizations
                connect_args={
                    "check_same_thread": False,
                    "timeout": 20,
                    # SQLite PRAGMA settings for performance
                    "isolation_level": None,  # Use autocommit mode
                } if "sqlite" in database_url else {},
                
                # Connection pool event listeners
                listeners=[
                    ("connect", self._on_connect),
                    ("checkout", self._on_checkout),
                    ("checkin", self._on_checkin)
                ]
            )
            
            # Set up optimized session factory
            self.session_factory = scoped_session(
                sessionmaker(
                    bind=self.engine,
                    autoflush=False,  # Manual control over flushing
                    autocommit=False,
                    expire_on_commit=False,  # Keep objects after commit
                )
            )
            
            # Apply database-specific optimizations
            await self._apply_database_optimizations()
            
            # Set up performance monitoring
            self._setup_performance_monitoring()
            
            logger.info(f"Enhanced database engine initialized with pool_size={self.config.pool_size}")
            
        except Exception as e:
            logger.error(f"Failed to initialize optimized database engine: {e}")
            raise
    
    def _on_connect(self, connection, connection_record):
        """Optimize new database connections."""
        try:
            if "sqlite" in str(connection.engine.url):
                # SQLite-specific optimizations
                connection.execute(text("PRAGMA journal_mode=WAL"))  # Write-Ahead Logging
                connection.execute(text("PRAGMA synchronous=NORMAL"))  # Balance safety/speed
                connection.execute(text("PRAGMA cache_size=10000"))  # 10MB cache
                connection.execute(text("PRAGMA temp_store=MEMORY"))  # Use memory for temp tables
                connection.execute(text("PRAGMA mmap_size=268435456"))  # 256MB memory mapping
                connection.execute(text("PRAGMA optimize"))  # Optimize statistics
                
                logger.debug("Applied SQLite performance optimizations to new connection")
            
            # General connection optimizations
            connection.execute(text("PRAGMA query_only=OFF"))
            
        except Exception as e:
            logger.warning(f"Failed to apply connection optimizations: {e}")
    
    def _on_checkout(self, connection, connection_record, connection_proxy):
        """Monitor connection checkout."""
        self.performance_stats["connection_pool_stats"]["checkouts"] = \
            self.performance_stats["connection_pool_stats"].get("checkouts", 0) + 1
    
    def _on_checkin(self, connection, connection_record):
        """Monitor connection checkin."""
        self.performance_stats["connection_pool_stats"]["checkins"] = \
            self.performance_stats["connection_pool_stats"].get("checkins", 0) + 1
    
    async def _apply_database_optimizations(self):
        """Apply database-level optimizations."""
        if not self.engine:
            return
        
        try:
            with self.engine.connect() as conn:
                # Apply SQLite-specific optimizations
                if "sqlite" in str(self.engine.url):
                    # Analyze tables for query optimization
                    conn.execute(text("ANALYZE"))
                    
                    # Create additional performance indexes if needed
                    await self._create_performance_indexes(conn)
                    
                    logger.info("Applied database-level optimizations")
                    
        except Exception as e:
            logger.error(f"Failed to apply database optimizations: {e}")
    
    async def _create_performance_indexes(self, conn):
        """Create additional performance-focused indexes."""
        try:
            # Performance-focused composite indexes
            performance_indexes = [
                # Job-related performance indexes
                "CREATE INDEX IF NOT EXISTS idx_jobs_user_status_created ON jobs(user_id, status, created_at)",
                "CREATE INDEX IF NOT EXISTS idx_jobs_status_updated ON jobs(status, updated_at)",
                "CREATE INDEX IF NOT EXISTS idx_jobs_created_desc ON jobs(created_at DESC)",
                
                # User activity indexes
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_event_time ON audit_logs(user_id, event_type, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_ip_time ON audit_logs(client_ip, timestamp)",
                
                # Search optimization indexes
                "CREATE INDEX IF NOT EXISTS idx_jobs_filename_search ON jobs(original_filename)",
                "CREATE INDEX IF NOT EXISTS idx_users_username_role ON users(username, role)",
                
                # Performance monitoring indexes
                "CREATE INDEX IF NOT EXISTS idx_perf_metrics_type_time ON performance_metrics(metric_type, timestamp DESC)",
                "CREATE INDEX IF NOT EXISTS idx_query_perf_endpoint_time ON query_performance_logs(endpoint, timestamp DESC)",
            ]
            
            for index_sql in performance_indexes:
                try:
                    conn.execute(text(index_sql))
                    logger.debug(f"Created performance index: {index_sql.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    # Index may already exist
                    logger.debug(f"Index creation skipped (may exist): {e}")
            
            # Commit index changes
            conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to create performance indexes: {e}")
    
    def _setup_performance_monitoring(self):
        """Set up query performance monitoring."""
        if not self.engine:
            return
        
        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            
            # Update performance statistics
            self.performance_stats["total_queries"] += 1
            
            # Track slow queries (>100ms)
            if total > 0.1:
                self.performance_stats["slow_queries"] += 1
                logger.warning(f"Slow query detected: {total:.3f}s - {statement[:100]}...")
            
            # Update average query time
            current_avg = self.performance_stats["avg_query_time"]
            total_queries = self.performance_stats["total_queries"]
            self.performance_stats["avg_query_time"] = (
                (current_avg * (total_queries - 1) + total) / total_queries
            )
    
    @asynccontextmanager
    async def get_optimized_session(self):
        """Get an optimized database session with proper cleanup."""
        if not self.session_factory:
            raise RuntimeError("Database optimizer not initialized")
        
        session = self.session_factory()
        try:
            # Configure session for optimal performance
            session.execute(text("PRAGMA query_only=OFF"))
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    async def get_connection_pool_status(self) -> Dict[str, Any]:
        """Get current connection pool status."""
        if not self.engine:
            return {"status": "not_initialized"}
        
        pool = self.engine.pool
        
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
            "total_connections": pool.size() + pool.overflow(),
            "utilization_percent": (pool.checkedout() / (pool.size() + pool.overflow())) * 100,
            "configuration": {
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "pool_timeout": self.config.pool_timeout,
                "pool_recycle": self.config.pool_recycle
            }
        }
    
    async def analyze_query_performance(self, session: Session) -> Dict[str, Any]:
        """Analyze current query performance patterns."""
        try:
            # Get slow query statistics
            slow_queries = session.execute(text("""
                SELECT 
                    query_type,
                    COUNT(*) as query_count,
                    AVG(execution_time_ms) as avg_time,
                    MAX(execution_time_ms) as max_time,
                    table_name
                FROM query_performance_logs 
                WHERE timestamp >= datetime('now', '-1 hour')
                GROUP BY query_type, table_name
                ORDER BY avg_time DESC
                LIMIT 20
            """)).fetchall()
            
            # Get table access patterns
            table_stats = session.execute(text("""
                SELECT 
                    table_name,
                    COUNT(*) as access_count,
                    AVG(execution_time_ms) as avg_access_time
                FROM query_performance_logs 
                WHERE timestamp >= datetime('now', '-1 hour')
                  AND table_name IS NOT NULL
                GROUP BY table_name
                ORDER BY access_count DESC
            """)).fetchall()
            
            return {
                "slow_queries": [
                    {
                        "query_type": row[0],
                        "count": row[1],
                        "avg_time_ms": row[2],
                        "max_time_ms": row[3],
                        "table": row[4]
                    } for row in slow_queries
                ],
                "table_access_patterns": [
                    {
                        "table": row[0],
                        "access_count": row[1],
                        "avg_time_ms": row[2]
                    } for row in table_stats
                ],
                "performance_summary": self.performance_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze query performance: {e}")
            return {"error": str(e)}
    
    async def optimize_database_maintenance(self, session: Session):
        """Perform database maintenance operations."""
        try:
            logger.info("Starting database maintenance optimization")
            
            # SQLite-specific maintenance
            if "sqlite" in str(self.engine.url):
                # Analyze tables for better query planning
                session.execute(text("ANALYZE"))
                
                # Vacuum if needed (reclaim space)
                result = session.execute(text("PRAGMA freelist_count")).fetchone()
                free_pages = result[0] if result else 0
                
                if free_pages > 1000:  # If more than 1000 free pages
                    logger.info(f"Running VACUUM (free pages: {free_pages})")
                    session.execute(text("VACUUM"))
                
                # Update table statistics
                session.execute(text("PRAGMA optimize"))
                
                logger.info("Database maintenance completed")
            
            # Update performance stats
            self.performance_stats["last_optimization"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.error(f"Database maintenance failed: {e}")
            raise

class AdvancedQueryPatterns:
    """Advanced query patterns for high-performance database operations."""
    
    @staticmethod
    async def bulk_insert_jobs(session: Session, job_data: List[Dict[str, Any]]) -> List[str]:
        """Efficiently insert multiple jobs using bulk operations."""
        try:
            # Prepare bulk insert data
            jobs = []
            for data in job_data:
                job = Job(
                    id=data["id"],
                    original_filename=data["filename"],
                    saved_filename=data["saved_filename"],
                    model=data.get("model", "small"),
                    status=JobStatusEnum.QUEUED
                )
                jobs.append(job)
            
            # Bulk insert with efficient batch processing
            session.bulk_save_objects(jobs)
            session.commit()
            
            job_ids = [job.id for job in jobs]
            logger.info(f"Bulk inserted {len(jobs)} jobs efficiently")
            
            return job_ids
            
        except Exception as e:
            session.rollback()
            logger.error(f"Bulk job insert failed: {e}")
            raise
    
    @staticmethod
    async def get_dashboard_data_optimized(session: Session, user_id: int) -> Dict[str, Any]:
        """Get dashboard data with a single optimized query."""
        try:
            # Single query for all dashboard statistics
            dashboard_query = session.execute(text("""
                WITH user_stats AS (
                    SELECT 
                        COUNT(*) as total_jobs,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_jobs,
                        SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing_jobs,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_jobs,
                        SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END) as queued_jobs,
                        MAX(created_at) as last_job_date,
                        AVG(CASE WHEN finished_at IS NOT NULL AND started_at IS NOT NULL 
                            THEN (julianday(finished_at) - julianday(started_at)) * 86400 
                            ELSE NULL END) as avg_processing_time
                    FROM jobs 
                    WHERE user_id = :user_id
                ),
                recent_activity AS (
                    SELECT COUNT(*) as recent_activity_count
                    FROM audit_logs 
                    WHERE user_id = :user_id 
                      AND timestamp >= datetime('now', '-7 days')
                )
                SELECT 
                    us.total_jobs,
                    us.completed_jobs,
                    us.processing_jobs,
                    us.failed_jobs,
                    us.queued_jobs,
                    us.last_job_date,
                    us.avg_processing_time,
                    ra.recent_activity_count
                FROM user_stats us, recent_activity ra
            """), {"user_id": user_id}).fetchone()
            
            if not dashboard_query:
                return {
                    "total_jobs": 0,
                    "completed_jobs": 0,
                    "processing_jobs": 0,
                    "failed_jobs": 0,
                    "queued_jobs": 0,
                    "success_rate": 0.0,
                    "avg_processing_time": 0.0,
                    "recent_activity_count": 0
                }
            
            # Calculate success rate
            total = dashboard_query[0] or 0
            completed = dashboard_query[1] or 0
            success_rate = (completed / total * 100) if total > 0 else 0.0
            
            return {
                "total_jobs": total,
                "completed_jobs": completed,
                "processing_jobs": dashboard_query[2] or 0,
                "failed_jobs": dashboard_query[3] or 0,
                "queued_jobs": dashboard_query[4] or 0,
                "success_rate": success_rate,
                "last_job_date": dashboard_query[5],
                "avg_processing_time": dashboard_query[6] or 0.0,
                "recent_activity_count": dashboard_query[7] or 0
            }
            
        except Exception as e:
            logger.error(f"Dashboard data query failed: {e}")
            raise
    
    @staticmethod
    async def search_jobs_optimized(session: Session, user_id: int, search_term: str, 
                                  limit: int = 20) -> List[Job]:
        """Optimized job search with full-text capabilities."""
        try:
            # Use optimized search with indexes
            search_pattern = f"%{search_term}%"
            
            jobs = session.query(Job).options(
                selectinload(Job.metadata)  # Eager load metadata
            ).filter(
                and_(
                    Job.user_id == user_id,
                    or_(
                        Job.original_filename.ilike(search_pattern),
                        Job.id.ilike(search_pattern),
                        Job.model.ilike(search_pattern)
                    )
                )
            ).order_by(
                desc(Job.created_at)
            ).limit(limit).all()
            
            logger.debug(f"Search query returned {len(jobs)} results for term: {search_term}")
            
            return jobs
            
        except Exception as e:
            logger.error(f"Job search failed: {e}")
            raise
    
    @staticmethod
    async def get_system_health_optimized(session: Session) -> Dict[str, Any]:
        """Get system health metrics with optimized queries."""
        try:
            # System health in single query
            health_data = session.execute(text("""
                WITH job_stats AS (
                    SELECT 
                        COUNT(*) as total_jobs,
                        SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as active_jobs,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_jobs,
                        SUM(CASE WHEN created_at >= datetime('now', '-1 hour') THEN 1 ELSE 0 END) as recent_jobs
                    FROM jobs
                ),
                user_stats AS (
                    SELECT 
                        COUNT(*) as total_users,
                        SUM(CASE WHEN created_at >= datetime('now', '-1 day') THEN 1 ELSE 0 END) as new_users_today
                    FROM users
                ),
                error_stats AS (
                    SELECT COUNT(*) as recent_errors
                    FROM audit_logs 
                    WHERE severity = 'high' 
                      AND timestamp >= datetime('now', '-1 hour')
                )
                SELECT 
                    js.total_jobs,
                    js.active_jobs,
                    js.failed_jobs,
                    js.recent_jobs,
                    us.total_users,
                    us.new_users_today,
                    es.recent_errors
                FROM job_stats js, user_stats us, error_stats es
            """)).fetchone()
            
            if not health_data:
                return {"status": "unknown", "metrics": {}}
            
            # Calculate health score
            total_jobs = health_data[0] or 0
            failed_jobs = health_data[2] or 0
            recent_errors = health_data[6] or 0
            
            failure_rate = (failed_jobs / total_jobs * 100) if total_jobs > 0 else 0
            health_score = max(0, 100 - failure_rate - (recent_errors * 5))
            
            return {
                "status": "healthy" if health_score > 80 else "degraded" if health_score > 50 else "critical",
                "health_score": health_score,
                "metrics": {
                    "total_jobs": total_jobs,
                    "active_jobs": health_data[1] or 0,
                    "failed_jobs": failed_jobs,
                    "recent_jobs": health_data[3] or 0,
                    "total_users": health_data[4] or 0,
                    "new_users_today": health_data[5] or 0,
                    "recent_errors": recent_errors,
                    "failure_rate": failure_rate
                }
            }
            
        except Exception as e:
            logger.error(f"System health query failed: {e}")
            return {"status": "error", "error": str(e)}

# Global database optimizer instance
db_optimizer: Optional[EnhancedDatabaseOptimizer] = None

async def initialize_database_optimizer(database_url: str, config: ConnectionPoolConfig = None):
    """Initialize the global database optimizer."""
    global db_optimizer
    
    db_optimizer = EnhancedDatabaseOptimizer(config)
    await db_optimizer.initialize_optimized_engine(database_url)
    
    logger.info("Enhanced database optimizer initialized")

async def get_database_optimizer() -> Optional[EnhancedDatabaseOptimizer]:
    """Get the global database optimizer instance."""
    return db_optimizer

async def cleanup_database_optimizer():
    """Cleanup the database optimizer."""
    global db_optimizer
    
    if db_optimizer and db_optimizer.engine:
        db_optimizer.engine.dispose()
        db_optimizer = None
        
    logger.info("Database optimizer cleaned up")
