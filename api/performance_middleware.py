"""
Database Performance Monitoring Middleware
Provides FastAPI middleware for database performance monitoring and optimization
"""

import time
import json
import asyncio
from typing import Callable, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from starlette.types import ASGIApp

from api.query_optimizer import DatabasePerformanceCollector, query_monitor


class DatabasePerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor database performance per request"""
    
    def __init__(
        self,
        app: ASGIApp,
        slow_request_threshold_ms: float = 1000.0,
        enable_detailed_logging: bool = True,
        enable_metrics_collection: bool = True
    ):
        super().__init__(app)
        self.slow_request_threshold_ms = slow_request_threshold_ms
        self.enable_detailed_logging = enable_detailed_logging
        self.enable_metrics_collection = enable_metrics_collection
        self.request_counter = 0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor database performance for each request"""
        start_time = time.time()
        self.request_counter += 1
        request_id = f"{int(start_time)}-{self.request_counter}"
        
        # Add request context for query monitoring
        request.state.request_id = request_id
        request.state.start_time = start_time
        request.state.query_count = 0
        request.state.total_query_time = 0.0
        
        # Store original database session for monitoring
        original_db = getattr(request.state, 'db', None)
        
        response = await call_next(request)
        
        # Calculate total request time
        total_time_ms = (time.time() - start_time) * 1000
        
        # Get database performance metrics from request state
        query_count = getattr(request.state, 'query_count', 0)
        total_query_time_ms = getattr(request.state, 'total_query_time', 0.0) * 1000
        
        # Add performance headers
        response.headers["X-Request-Time-Ms"] = str(round(total_time_ms, 2))
        response.headers["X-Query-Count"] = str(query_count)
        response.headers["X-Query-Time-Ms"] = str(round(total_query_time_ms, 2))
        
        # Log slow requests
        if total_time_ms > self.slow_request_threshold_ms and self.enable_detailed_logging:
            await self._log_slow_request(request, response, total_time_ms, query_count, total_query_time_ms)
        
        # Collect performance metrics
        if self.enable_metrics_collection and original_db:
            await self._collect_performance_metrics(
                original_db, request, total_time_ms, query_count, total_query_time_ms
            )
        
        return response
    
    async def _log_slow_request(self, request: Request, response: Response, 
                               total_time_ms: float, query_count: int, query_time_ms: float):
        """Log details of slow requests"""
        print(f"SLOW REQUEST: {request.method} {request.url.path}")
        print(f"  Total Time: {total_time_ms:.2f}ms")
        print(f"  Query Count: {query_count}")
        print(f"  Query Time: {query_time_ms:.2f}ms")
        print(f"  Status Code: {response.status_code}")
        print(f"  User Agent: {request.headers.get('user-agent', 'Unknown')}")
    
    async def _collect_performance_metrics(self, db: Session, request: Request, 
                                          total_time_ms: float, query_count: int, 
                                          query_time_ms: float):
        """Collect performance metrics to database"""
        try:
            # Collect request-level metrics
            DatabasePerformanceCollector.record_metric(
                db=db,
                metric_type="request_performance",
                metric_name="request_duration",
                value=total_time_ms,
                unit="milliseconds",
                tags={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "status_code": str(getattr(request.state, 'response_status_code', 0))
                }
            )
            
            DatabasePerformanceCollector.record_metric(
                db=db,
                metric_type="database_performance",
                metric_name="queries_per_request",
                value=query_count,
                unit="count",
                tags={
                    "endpoint": request.url.path,
                    "method": request.method
                }
            )
            
            if query_count > 0:
                DatabasePerformanceCollector.record_metric(
                    db=db,
                    metric_type="database_performance",
                    metric_name="query_time_per_request",
                    value=query_time_ms,
                    unit="milliseconds",
                    tags={
                        "endpoint": request.url.path,
                        "method": request.method
                    }
                )
        except Exception as e:
            print(f"Failed to collect performance metrics: {e}")


class DatabaseQueryCounter:
    """Context manager to count and time database queries"""
    
    def __init__(self, request: Request):
        self.request = request
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            query_time = time.time() - self.start_time
            
            # Update request state
            current_count = getattr(self.request.state, 'query_count', 0)
            current_time = getattr(self.request.state, 'total_query_time', 0.0)
            
            self.request.state.query_count = current_count + 1
            self.request.state.total_query_time = current_time + query_time


def setup_database_monitoring(app: FastAPI, config: Optional[Dict[str, Any]] = None):
    """Setup database performance monitoring for FastAPI app"""
    
    # Default configuration
    default_config = {
        "slow_request_threshold_ms": 1000.0,
        "enable_detailed_logging": True,
        "enable_metrics_collection": True,
        "slow_query_threshold_ms": 100.0
    }
    
    if config:
        default_config.update(config)
    
    # Configure query monitor
    query_monitor.slow_query_threshold_ms = default_config["slow_query_threshold_ms"]
    query_monitor.enabled = default_config["enable_metrics_collection"]
    
    # Add performance monitoring middleware
    app.add_middleware(
        DatabasePerformanceMiddleware,
        slow_request_threshold_ms=default_config["slow_request_threshold_ms"],
        enable_detailed_logging=default_config["enable_detailed_logging"],
        enable_metrics_collection=default_config["enable_metrics_collection"]
    )
    
    # Add performance monitoring endpoints
    @app.get("/admin/performance/summary")
    async def get_performance_summary(hours: int = 24, db: Session = None):
        """Get database performance summary"""
        if not db:
            return {"error": "Database session not available"}
        
        return DatabasePerformanceCollector.get_performance_summary(db, hours)
    
    @app.get("/admin/performance/queries")
    async def get_slow_queries(limit: int = 50, min_duration_ms: float = 100.0, db: Session = None):
        """Get slow query analysis"""
        if not db:
            return {"error": "Database session not available"}
        
        from api.models import QueryPerformanceLog
        from sqlalchemy import desc
        
        slow_queries = db.query(QueryPerformanceLog).filter(
            QueryPerformanceLog.execution_time_ms >= min_duration_ms
        ).order_by(desc(QueryPerformanceLog.execution_time_ms)).limit(limit).all()
        
        return [
            {
                "timestamp": query.timestamp.isoformat(),
                "query_type": query.query_type,
                "execution_time_ms": query.execution_time_ms,
                "table_name": query.table_name,
                "endpoint": query.endpoint,
                "query_text": query.query_text[:200] + "..." if len(query.query_text) > 200 else query.query_text
            }
            for query in slow_queries
        ]
    
    @app.get("/admin/performance/metrics")
    async def get_performance_metrics(hours: int = 24, metric_type: Optional[str] = None, db: Session = None):
        """Get performance metrics"""
        if not db:
            return {"error": "Database session not available"}
        
        from api.models import PerformanceMetric
        from sqlalchemy import desc, and_
        from datetime import datetime, timedelta
        
        since_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(PerformanceMetric).filter(PerformanceMetric.timestamp >= since_time)
        
        if metric_type:
            query = query.filter(PerformanceMetric.metric_type == metric_type)
        
        metrics = query.order_by(desc(PerformanceMetric.timestamp)).limit(1000).all()
        
        return [
            {
                "timestamp": metric.timestamp.isoformat(),
                "metric_type": metric.metric_type,
                "metric_name": metric.metric_name,
                "value": metric.value,
                "unit": metric.unit,
                "tags": json.loads(metric.tags) if metric.tags else None
            }
            for metric in metrics
        ]


# ────────────────────────────────────────────────────────────────────────────
# Database Session Performance Wrapper
# ────────────────────────────────────────────────────────────────────────────

class PerformanceAwareSession(Session):
    """Session wrapper that tracks query performance"""
    
    def __init__(self, *args, request: Optional[Request] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self._query_count = 0
        self._total_query_time = 0.0
    
    def execute(self, statement, parameters=None, execution_options=None, bind=None, _parent_execute_state=None, _add_event=None):
        """Override execute to track performance"""
        start_time = time.time()
        
        try:
            result = super().execute(statement, parameters, execution_options, bind, _parent_execute_state, _add_event)
            return result
        finally:
            execution_time = time.time() - start_time
            self._query_count += 1
            self._total_query_time += execution_time
            
            # Update request state if available
            if self.request:
                self.request.state.query_count = getattr(self.request.state, 'query_count', 0) + 1
                self.request.state.total_query_time = getattr(self.request.state, 'total_query_time', 0.0) + execution_time
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for this session"""
        return {
            "query_count": self._query_count,
            "total_query_time_seconds": self._total_query_time,
            "average_query_time_ms": (self._total_query_time / max(self._query_count, 1)) * 1000
        }
