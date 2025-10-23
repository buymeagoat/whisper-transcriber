"""
Database Query Optimization Utilities
Provides optimized query patterns and utilities to prevent N+1 queries and improve performance
"""

import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime, timedelta

from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.orm import Session, joinedload, selectinload, contains_eager
from sqlalchemy.orm.query import Query
from sqlalchemy.engine import Engine
from sqlalchemy import event

from api.models import Job, User, TranscriptMetadata, AuditLog, PerformanceMetric, QueryPerformanceLog


# ────────────────────────────────────────────────────────────────────────────
# Query Performance Monitoring
# ────────────────────────────────────────────────────────────────────────────

class QueryPerformanceMonitor:
    """Monitor and log database query performance"""
    
    def __init__(self, slow_query_threshold_ms: float = 100.0):
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.enabled = True
    
    def log_slow_query(self, db: Session, query_type: str, execution_time_ms: float, 
                      query_text: str, table_name: Optional[str] = None,
                      user_id: Optional[int] = None, endpoint: Optional[str] = None,
                      row_count: Optional[int] = None):
        """Log slow queries for analysis"""
        if not self.enabled or execution_time_ms < self.slow_query_threshold_ms:
            return
            
        try:
            log_entry = QueryPerformanceLog(
                timestamp=datetime.utcnow(),
                query_type=query_type,
                execution_time_ms=execution_time_ms,
                query_text=query_text[:2000],  # Truncate long queries
                table_name=table_name,
                user_id=user_id,
                endpoint=endpoint,
                row_count=row_count
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            # Don't let logging errors break the application
            print(f"Failed to log slow query: {e}")
    
    @contextmanager
    def monitor_query(self, db: Session, query_type: str, table_name: Optional[str] = None,
                     user_id: Optional[int] = None, endpoint: Optional[str] = None):
        """Context manager to monitor query execution time"""
        start_time = time.time()
        row_count = None
        query_text = ""
        
        try:
            yield
        finally:
            execution_time_ms = (time.time() - start_time) * 1000
            self.log_slow_query(
                db=db,
                query_type=query_type,
                execution_time_ms=execution_time_ms,
                query_text=query_text,
                table_name=table_name,
                user_id=user_id,
                endpoint=endpoint,
                row_count=row_count
            )


# Global performance monitor instance
query_monitor = QueryPerformanceMonitor()


def performance_tracked(query_type: str, table_name: Optional[str] = None):
    """Decorator to track query performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            db = kwargs.get('db') or (args[0] if args and hasattr(args[0], 'query') else None)
            user_id = kwargs.get('user_id')
            endpoint = kwargs.get('endpoint')
            
            if db:
                with query_monitor.monitor_query(db, query_type, table_name, user_id, endpoint):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator


# ────────────────────────────────────────────────────────────────────────────
# Optimized Query Patterns
# ────────────────────────────────────────────────────────────────────────────

class OptimizedJobQueries:
    """Optimized query patterns for Job model to prevent N+1 queries"""
    
    @staticmethod
    @performance_tracked("SELECT", "jobs")
    def get_jobs_with_metadata(db: Session, user_id: Optional[int] = None, 
                              status: Optional[str] = None, limit: int = 20, 
                              offset: int = 0) -> List[Job]:
        """Get jobs with metadata in a single query using eager loading"""
        query = db.query(Job).options(
            selectinload(Job.metadata)  # Prevent N+1 query for metadata
        )
        
        # Apply filters
        if user_id:
            query = query.filter(Job.user_id == user_id)
        if status:
            query = query.filter(Job.status == status)
        
        # Order by created_at desc for latest first
        query = query.order_by(desc(Job.created_at))
        
        # Apply pagination
        return query.offset(offset).limit(limit).all()
    
    @staticmethod
    @performance_tracked("SELECT", "jobs")
    def get_job_with_user_and_metadata(db: Session, job_id: str) -> Optional[Job]:
        """Get single job with user and metadata in one query"""
        return db.query(Job).options(
            joinedload(Job.user),
            joinedload(Job.metadata)
        ).filter(Job.id == job_id).first()
    
    @staticmethod
    @performance_tracked("SELECT", "jobs")
    def get_jobs_by_user_paginated(db: Session, user_id: int, page: int = 1, 
                                  page_size: int = 20, status: Optional[str] = None) -> Tuple[List[Job], int]:
        """Get user's jobs with pagination and total count"""
        base_query = db.query(Job).filter(Job.user_id == user_id)
        
        if status:
            base_query = base_query.filter(Job.status == status)
        
        # Get total count
        total_count = base_query.count()
        
        # Get paginated results
        offset = (page - 1) * page_size
        jobs = base_query.order_by(desc(Job.created_at)).offset(offset).limit(page_size).all()
        
        return jobs, total_count
    
    @staticmethod
    @performance_tracked("SELECT", "jobs")
    def get_job_statistics(db: Session, user_id: Optional[int] = None, 
                          days: int = 30) -> Dict[str, Any]:
        """Get job statistics efficiently with single query"""
        base_query = db.query(Job)
        
        if user_id:
            base_query = base_query.filter(Job.user_id == user_id)
        
        # Filter by date range
        since_date = datetime.utcnow() - timedelta(days=days)
        base_query = base_query.filter(Job.created_at >= since_date)
        
        # Get statistics in single query using aggregation
        stats = db.query(
            func.count(Job.id).label('total_jobs'),
            func.sum(func.case([(Job.status == 'completed', 1)], else_=0)).label('completed_jobs'),
            func.sum(func.case([(Job.status == 'failed', 1)], else_=0)).label('failed_jobs'),
            func.sum(func.case([(Job.status == 'processing', 1)], else_=0)).label('processing_jobs'),
            func.sum(func.case([(Job.status == 'queued', 1)], else_=0)).label('queued_jobs'),
            func.avg(Job.processing_time_seconds).label('avg_processing_time'),
            func.avg(Job.file_size_bytes).label('avg_file_size')
        ).filter(Job.created_at >= since_date)
        
        if user_id:
            stats = stats.filter(Job.user_id == user_id)
        
        result = stats.first()
        
        return {
            'total_jobs': result.total_jobs or 0,
            'completed_jobs': result.completed_jobs or 0,
            'failed_jobs': result.failed_jobs or 0,
            'processing_jobs': result.processing_jobs or 0,
            'queued_jobs': result.queued_jobs or 0,
            'avg_processing_time_seconds': float(result.avg_processing_time or 0),
            'avg_file_size_bytes': int(result.avg_file_size or 0),
            'success_rate': (result.completed_jobs or 0) / max(result.total_jobs or 1, 1) * 100
        }
    
    @staticmethod
    @performance_tracked("SELECT", "jobs")
    def get_recent_active_jobs(db: Session, limit: int = 10) -> List[Job]:
        """Get recently active jobs efficiently"""
        return db.query(Job).filter(
            Job.status.in_(['processing', 'queued'])
        ).order_by(desc(Job.updated_at)).limit(limit).all()


class OptimizedUserQueries:
    """Optimized query patterns for User model"""
    
    @staticmethod
    @performance_tracked("SELECT", "users")
    def get_active_users_with_stats(db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        """Get active users with their job statistics"""
        # Use subquery to get job counts per user
        job_stats = db.query(
            Job.user_id,
            func.count(Job.id).label('total_jobs'),
            func.sum(func.case([(Job.status == 'completed', 1)], else_=0)).label('completed_jobs'),
            func.max(Job.created_at).label('last_job_date')
        ).group_by(Job.user_id).subquery()
        
        # Join users with job statistics
        users_with_stats = db.query(
            User,
            func.coalesce(job_stats.c.total_jobs, 0).label('total_jobs'),
            func.coalesce(job_stats.c.completed_jobs, 0).label('completed_jobs'),
            job_stats.c.last_job_date
        ).outerjoin(
            job_stats, User.id == job_stats.c.user_id
        ).filter(
            User.is_active == True
        ).order_by(desc(User.last_login)).limit(limit).all()
        
        return [
            {
                'user': user,
                'total_jobs': total_jobs,
                'completed_jobs': completed_jobs,
                'last_job_date': last_job_date,
                'success_rate': (completed_jobs / max(total_jobs, 1)) * 100 if total_jobs > 0 else 0
            }
            for user, total_jobs, completed_jobs, last_job_date in users_with_stats
        ]
    
    @staticmethod
    @performance_tracked("SELECT", "users")
    def get_user_by_username_optimized(db: Session, username: str) -> Optional[User]:
        """Get user by username with optimized query"""
        return db.query(User).filter(
            and_(User.username == username, User.is_active == True)
        ).first()


class OptimizedMetadataQueries:
    """Optimized query patterns for TranscriptMetadata"""
    
    @staticmethod
    @performance_tracked("SELECT", "metadata")
    def get_metadata_analytics(db: Session, days: int = 30) -> Dict[str, Any]:
        """Get metadata analytics efficiently"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        stats = db.query(
            func.count(TranscriptMetadata.job_id).label('total_transcripts'),
            func.avg(TranscriptMetadata.duration).label('avg_duration'),
            func.avg(TranscriptMetadata.tokens).label('avg_tokens'),
            func.avg(TranscriptMetadata.wpm).label('avg_wpm'),
            func.avg(TranscriptMetadata.sentiment).label('avg_sentiment')
        ).join(Job).filter(Job.created_at >= since_date).first()
        
        # Get language distribution
        language_stats = db.query(
            TranscriptMetadata.language,
            func.count(TranscriptMetadata.job_id).label('count')
        ).join(Job).filter(
            Job.created_at >= since_date
        ).group_by(TranscriptMetadata.language).all()
        
        return {
            'total_transcripts': stats.total_transcripts or 0,
            'avg_duration_seconds': float(stats.avg_duration or 0),
            'avg_tokens': float(stats.avg_tokens or 0),
            'avg_wpm': float(stats.avg_wpm or 0),
            'avg_sentiment': float(stats.avg_sentiment or 0),
            'language_distribution': {lang: count for lang, count in language_stats if lang}
        }


class OptimizedAuditLogQueries:
    """Optimized query patterns for AuditLog"""
    
    @staticmethod
    @performance_tracked("SELECT", "audit_logs")
    def get_security_events(db: Session, hours: int = 24, severity: Optional[str] = None,
                           limit: int = 100) -> List[AuditLog]:
        """Get recent security events efficiently"""
        since_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(AuditLog).filter(AuditLog.timestamp >= since_time)
        
        if severity:
            query = query.filter(AuditLog.severity == severity)
        
        return query.order_by(desc(AuditLog.timestamp)).limit(limit).all()
    
    @staticmethod
    @performance_tracked("SELECT", "audit_logs")
    def get_user_activity_summary(db: Session, user_id: int, days: int = 7) -> Dict[str, Any]:
        """Get user activity summary efficiently"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        activity = db.query(
            func.count(AuditLog.id).label('total_events'),
            func.count(func.distinct(AuditLog.client_ip)).label('unique_ips'),
            func.count(func.distinct(AuditLog.session_id)).label('unique_sessions'),
            func.max(AuditLog.timestamp).label('last_activity')
        ).filter(
            and_(AuditLog.user_id == user_id, AuditLog.timestamp >= since_date)
        ).first()
        
        return {
            'total_events': activity.total_events or 0,
            'unique_ips': activity.unique_ips or 0,
            'unique_sessions': activity.unique_sessions or 0,
            'last_activity': activity.last_activity
        }


# ────────────────────────────────────────────────────────────────────────────
# Database Performance Utilities
# ────────────────────────────────────────────────────────────────────────────

class DatabasePerformanceCollector:
    """Collect and store database performance metrics"""
    
    @staticmethod
    def record_metric(db: Session, metric_type: str, metric_name: str, 
                     value: float, unit: Optional[str] = None, 
                     tags: Optional[Dict[str, str]] = None):
        """Record a performance metric"""
        try:
            tags_json = None
            if tags:
                import json
                tags_json = json.dumps(tags)
            
            metric = PerformanceMetric(
                timestamp=datetime.utcnow(),
                metric_type=metric_type,
                metric_name=metric_name,
                value=value,
                unit=unit,
                tags=tags_json
            )
            db.add(metric)
            db.commit()
        except Exception as e:
            print(f"Failed to record performance metric: {e}")
    
    @staticmethod
    def get_performance_summary(db: Session, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        since_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get query performance stats
        query_stats = db.query(
            func.count(QueryPerformanceLog.id).label('total_queries'),
            func.avg(QueryPerformanceLog.execution_time_ms).label('avg_execution_time'),
            func.max(QueryPerformanceLog.execution_time_ms).label('max_execution_time'),
            func.count(
                func.case([(QueryPerformanceLog.execution_time_ms > 100, 1)], else_=None)
            ).label('slow_queries')
        ).filter(QueryPerformanceLog.timestamp >= since_time).first()
        
        # Get top slow queries
        slow_queries = db.query(
            QueryPerformanceLog.query_type,
            QueryPerformanceLog.table_name,
            func.avg(QueryPerformanceLog.execution_time_ms).label('avg_time'),
            func.count(QueryPerformanceLog.id).label('count')
        ).filter(
            QueryPerformanceLog.timestamp >= since_time
        ).group_by(
            QueryPerformanceLog.query_type,
            QueryPerformanceLog.table_name
        ).order_by(desc('avg_time')).limit(10).all()
        
        return {
            'total_queries': query_stats.total_queries or 0,
            'avg_execution_time_ms': float(query_stats.avg_execution_time or 0),
            'max_execution_time_ms': float(query_stats.max_execution_time or 0),
            'slow_queries_count': query_stats.slow_queries or 0,
            'slow_query_percentage': (query_stats.slow_queries or 0) / max(query_stats.total_queries or 1, 1) * 100,
            'top_slow_queries': [
                {
                    'query_type': query_type,
                    'table_name': table_name,
                    'avg_time_ms': float(avg_time),
                    'count': count
                }
                for query_type, table_name, avg_time, count in slow_queries
            ]
        }


# ────────────────────────────────────────────────────────────────────────────
# SQLAlchemy Event Listeners for Automatic Performance Tracking
# ────────────────────────────────────────────────────────────────────────────

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time"""
    context._query_start_time = time.time()


@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query execution time"""
    if hasattr(context, '_query_start_time'):
        execution_time = time.time() - context._query_start_time
        execution_time_ms = execution_time * 1000
        
        # Log slow queries (>100ms)
        if execution_time_ms > 100:
            print(f"SLOW QUERY ({execution_time_ms:.2f}ms): {statement[:200]}...")


# ────────────────────────────────────────────────────────────────────────────
# Connection Pool Monitoring
# ────────────────────────────────────────────────────────────────────────────

def get_connection_pool_status(engine: Engine) -> Dict[str, Any]:
    """Get connection pool status for monitoring"""
    pool = engine.pool
    
    return {
        'pool_size': pool.size(),
        'checked_in': pool.checkedin(),
        'checked_out': pool.checkedout(),
        'overflow': pool.overflow(),
        'invalid': pool.invalid()
    }
