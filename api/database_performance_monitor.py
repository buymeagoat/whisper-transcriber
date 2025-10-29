"""
Enhanced Database Performance Monitoring - I005 Infrastructure Issue
Comprehensive database performance monitoring with real-time metrics and alerting
"""

import time
import asyncio
import threading
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from functools import wraps

from sqlalchemy import event, create_engine, text, func
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import Pool

from api.orm_bootstrap import SessionLocal, engine
from api.models import PerformanceMetric, QueryPerformanceLog
from api.utils.logger import get_system_logger

logger = get_system_logger("db_monitor")


@dataclass
class PerformanceThresholds:
    """Performance monitoring thresholds"""
    slow_query_ms: float = 100.0
    very_slow_query_ms: float = 500.0
    connection_timeout_ms: float = 5000.0
    high_cpu_percentage: float = 80.0
    low_throughput_ops_per_sec: float = 1.0
    high_error_rate_percentage: float = 5.0


@dataclass
class ConnectionPoolMetrics:
    """Connection pool performance metrics"""
    pool_size: int
    checked_out: int
    checked_in: int
    overflow: int
    invalid: int
    utilization_percentage: float
    timestamp: datetime


@dataclass
class QueryMetrics:
    """Individual query performance metrics"""
    query_id: str
    query_type: str
    table_name: Optional[str]
    execution_time_ms: float
    row_count: Optional[int]
    timestamp: datetime
    success: bool
    error_message: Optional[str]


class DatabasePerformanceMonitor:
    """Enhanced database performance monitoring with real-time metrics"""
    
    def __init__(self, thresholds: Optional[PerformanceThresholds] = None):
        self.thresholds = thresholds or PerformanceThresholds()
        self.metrics_buffer = []
        self.connection_pool_history = []
        self.query_metrics_history = []
        self.performance_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "failed_queries": 0,
            "avg_query_time": 0.0,
            "queries_per_second": 0.0,
            "last_reset": datetime.utcnow()
        }
        
        # Alert handlers
        self.alert_handlers: List[Callable[[str, Dict[str, Any]], None]] = []
        
        # Monitoring controls
        self.monitoring_active = False
        self.collection_thread = None
        
        # Install event listeners
        self._install_event_listeners()
    
    def _install_event_listeners(self):
        """Install SQLAlchemy event listeners for automatic monitoring"""
        
        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Record query start time"""
            context._query_start_time = time.time()
            context._query_statement = statement
        
        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Record query completion and metrics"""
            if hasattr(context, '_query_start_time'):
                execution_time = time.time() - context._query_start_time
                execution_time_ms = execution_time * 1000
                
                # Update performance stats
                self.performance_stats["total_queries"] += 1
                
                if execution_time_ms > self.thresholds.slow_query_ms:
                    self.performance_stats["slow_queries"] += 1
                
                # Calculate rolling average
                current_avg = self.performance_stats["avg_query_time"]
                total_queries = self.performance_stats["total_queries"]
                self.performance_stats["avg_query_time"] = (
                    (current_avg * (total_queries - 1) + execution_time_ms) / total_queries
                )
                
                # Create query metrics
                query_metrics = QueryMetrics(
                    query_id=f"q_{int(time.time()*1000)}_{id(context)}",
                    query_type=self._determine_query_type(statement),
                    table_name=self._extract_table_name(statement),
                    execution_time_ms=execution_time_ms,
                    row_count=getattr(cursor, 'rowcount', None) if hasattr(cursor, 'rowcount') else None,
                    timestamp=datetime.utcnow(),
                    success=True,
                    error_message=None
                )
                
                self._record_query_metrics(query_metrics)
                
                # Check for alerts
                if execution_time_ms > self.thresholds.very_slow_query_ms:
                    self._trigger_alert("very_slow_query", {
                        "execution_time_ms": execution_time_ms,
                        "query": statement[:200],
                        "threshold": self.thresholds.very_slow_query_ms
                    })
        
        @event.listens_for(Engine, "handle_error")
        def receive_handle_error(exception_context):
            """Record query errors"""
            self.performance_stats["failed_queries"] += 1
            
            query_metrics = QueryMetrics(
                query_id=f"e_{int(time.time()*1000)}_{id(exception_context)}",
                query_type="ERROR",
                table_name=None,
                execution_time_ms=0.0,
                row_count=None,
                timestamp=datetime.utcnow(),
                success=False,
                error_message=str(exception_context.original_exception)
            )
            
            self._record_query_metrics(query_metrics)
            
            # Check error rate
            self._check_error_rate()
    
    def _determine_query_type(self, statement: str) -> str:
        """Determine query type from SQL statement"""
        statement_upper = statement.strip().upper()
        
        if statement_upper.startswith('SELECT'):
            return 'SELECT'
        elif statement_upper.startswith('INSERT'):
            return 'INSERT'
        elif statement_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif statement_upper.startswith('DELETE'):
            return 'DELETE'
        elif statement_upper.startswith('CREATE'):
            return 'CREATE'
        elif statement_upper.startswith('DROP'):
            return 'DROP'
        elif statement_upper.startswith('ALTER'):
            return 'ALTER'
        else:
            return 'OTHER'
    
    def _extract_table_name(self, statement: str) -> Optional[str]:
        """Extract table name from SQL statement"""
        try:
            statement_upper = statement.strip().upper()
            
            # Simple extraction for common patterns
            if 'FROM ' in statement_upper:
                parts = statement_upper.split('FROM ')[1].split()
                if parts:
                    return parts[0].strip('`"[]').lower()
            
            if 'INTO ' in statement_upper:
                parts = statement_upper.split('INTO ')[1].split()
                if parts:
                    return parts[0].strip('`"[]').lower()
            
            if 'UPDATE ' in statement_upper:
                parts = statement_upper.split('UPDATE ')[1].split()
                if parts:
                    return parts[0].strip('`"[]').lower()
                    
        except Exception:
            pass
        
        return None
    
    def _record_query_metrics(self, metrics: QueryMetrics):
        """Record query metrics in buffer"""
        self.query_metrics_history.append(metrics)
        
        # Keep only recent metrics (last 1000 queries)
        if len(self.query_metrics_history) > 1000:
            self.query_metrics_history = self.query_metrics_history[-1000:]
    
    def _trigger_alert(self, alert_type: str, context: Dict[str, Any]):
        """Trigger performance alert"""
        alert_data = {
            "type": alert_type,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context,
            "thresholds": {
                "slow_query_ms": self.thresholds.slow_query_ms,
                "very_slow_query_ms": self.thresholds.very_slow_query_ms
            }
        }
        
        logger.warning(f"Performance Alert [{alert_type}]: {context}")
        
        # Call registered alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert_type, alert_data)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    def _check_error_rate(self):
        """Check if error rate exceeds threshold"""
        total_queries = self.performance_stats["total_queries"]
        failed_queries = self.performance_stats["failed_queries"]
        
        if total_queries > 10:  # Only check after minimum queries
            error_rate = (failed_queries / total_queries) * 100
            
            if error_rate > self.thresholds.high_error_rate_percentage:
                self._trigger_alert("high_error_rate", {
                    "error_rate_percentage": error_rate,
                    "failed_queries": failed_queries,
                    "total_queries": total_queries,
                    "threshold": self.thresholds.high_error_rate_percentage
                })
    
    def collect_connection_pool_metrics(self) -> ConnectionPoolMetrics:
        """Collect current connection pool metrics"""
        try:
            pool = engine.pool
            
            # Get pool statistics
            pool_size = getattr(pool, '_pool_size', 0) or getattr(pool, 'size', lambda: 0)()
            checked_out = getattr(pool, 'checkedout', lambda: 0)()
            checked_in = getattr(pool, 'checkedin', lambda: 0)()
            overflow = getattr(pool, 'overflow', lambda: 0)()
            invalid = getattr(pool, 'invalid', lambda: 0)()
            
            # Calculate utilization
            if pool_size > 0:
                utilization = (checked_out / pool_size) * 100
            else:
                utilization = 0.0
            
            metrics = ConnectionPoolMetrics(
                pool_size=pool_size,
                checked_out=checked_out,
                checked_in=checked_in,
                overflow=overflow,
                invalid=invalid,
                utilization_percentage=utilization,
                timestamp=datetime.utcnow()
            )
            
            # Store in history
            self.connection_pool_history.append(metrics)
            
            # Keep only recent history (last 100 measurements)
            if len(self.connection_pool_history) > 100:
                self.connection_pool_history = self.connection_pool_history[-100:]
            
            # Check for alerts
            if utilization > 90:
                self._trigger_alert("high_connection_pool_usage", {
                    "utilization_percentage": utilization,
                    "checked_out": checked_out,
                    "pool_size": pool_size
                })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect connection pool metrics: {e}")
            return ConnectionPoolMetrics(0, 0, 0, 0, 0, 0.0, datetime.utcnow())
    
    def get_performance_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """Get performance summary for the last N minutes"""
        since = datetime.utcnow() - timedelta(minutes=minutes)
        
        # Filter recent queries
        recent_queries = [
            q for q in self.query_metrics_history 
            if q.timestamp >= since
        ]
        
        if not recent_queries:
            return {
                "period_minutes": minutes,
                "no_data": True
            }
        
        # Calculate metrics
        total_queries = len(recent_queries)
        successful_queries = len([q for q in recent_queries if q.success])
        failed_queries = total_queries - successful_queries
        
        execution_times = [q.execution_time_ms for q in recent_queries if q.success]
        
        if execution_times:
            import statistics
            avg_time = statistics.mean(execution_times)
            median_time = statistics.median(execution_times)
            max_time = max(execution_times)
            min_time = min(execution_times)
        else:
            avg_time = median_time = max_time = min_time = 0.0
        
        # Slow query analysis
        slow_queries = [q for q in recent_queries if q.execution_time_ms > self.thresholds.slow_query_ms]
        very_slow_queries = [q for q in recent_queries if q.execution_time_ms > self.thresholds.very_slow_query_ms]
        
        # Query type breakdown
        query_types = {}
        for query in recent_queries:
            query_type = query.query_type
            if query_type not in query_types:
                query_types[query_type] = {"count": 0, "avg_time": 0.0, "errors": 0}
            
            query_types[query_type]["count"] += 1
            if query.success:
                current_avg = query_types[query_type]["avg_time"]
                current_count = query_types[query_type]["count"]
                query_types[query_type]["avg_time"] = (
                    (current_avg * (current_count - 1) + query.execution_time_ms) / current_count
                )
            else:
                query_types[query_type]["errors"] += 1
        
        # Recent connection pool metrics
        recent_pool_metrics = [
            m for m in self.connection_pool_history 
            if m.timestamp >= since
        ]
        
        avg_pool_utilization = 0.0
        max_pool_utilization = 0.0
        if recent_pool_metrics:
            avg_pool_utilization = sum(m.utilization_percentage for m in recent_pool_metrics) / len(recent_pool_metrics)
            max_pool_utilization = max(m.utilization_percentage for m in recent_pool_metrics)
        
        return {
            "period_minutes": minutes,
            "timestamp": datetime.utcnow().isoformat(),
            "query_performance": {
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "failed_queries": failed_queries,
                "success_rate": (successful_queries / total_queries * 100) if total_queries > 0 else 0,
                "queries_per_minute": total_queries / minutes if minutes > 0 else 0,
                "avg_execution_time_ms": avg_time,
                "median_execution_time_ms": median_time,
                "min_execution_time_ms": min_time,
                "max_execution_time_ms": max_time,
                "slow_queries": len(slow_queries),
                "very_slow_queries": len(very_slow_queries),
                "slow_query_percentage": (len(slow_queries) / total_queries * 100) if total_queries > 0 else 0
            },
            "query_type_breakdown": query_types,
            "connection_pool": {
                "avg_utilization_percentage": avg_pool_utilization,
                "max_utilization_percentage": max_pool_utilization,
                "current_metrics": self.collect_connection_pool_metrics().__dict__ if self.connection_pool_history else None
            },
            "thresholds": {
                "slow_query_ms": self.thresholds.slow_query_ms,
                "very_slow_query_ms": self.thresholds.very_slow_query_ms,
                "high_error_rate_percentage": self.thresholds.high_error_rate_percentage
            }
        }
    
    def get_top_slow_queries(self, limit: int = 10, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get top slow queries from recent history"""
        since = datetime.utcnow() - timedelta(minutes=minutes)
        
        recent_queries = [
            q for q in self.query_metrics_history 
            if q.timestamp >= since and q.success
        ]
        
        # Sort by execution time and get top N
        slow_queries = sorted(recent_queries, key=lambda q: q.execution_time_ms, reverse=True)[:limit]
        
        return [
            {
                "query_id": q.query_id,
                "query_type": q.query_type,
                "table_name": q.table_name,
                "execution_time_ms": q.execution_time_ms,
                "timestamp": q.timestamp.isoformat(),
                "row_count": q.row_count
            }
            for q in slow_queries
        ]
    
    def register_alert_handler(self, handler: Callable[[str, Dict[str, Any]], None]):
        """Register an alert handler function"""
        self.alert_handlers.append(handler)
    
    def start_monitoring(self, collection_interval_seconds: int = 30):
        """Start background monitoring collection"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        def monitoring_loop():
            """Background monitoring loop"""
            while self.monitoring_active:
                try:
                    # Collect connection pool metrics
                    self.collect_connection_pool_metrics()
                    
                    # Calculate queries per second
                    current_time = time.time()
                    time_since_reset = (datetime.utcnow() - self.performance_stats["last_reset"]).total_seconds()
                    
                    if time_since_reset > 0:
                        self.performance_stats["queries_per_second"] = (
                            self.performance_stats["total_queries"] / time_since_reset
                        )
                    
                    # Check throughput
                    if (time_since_reset > 60 and  # After at least 1 minute
                        self.performance_stats["queries_per_second"] < self.thresholds.low_throughput_ops_per_sec):
                        self._trigger_alert("low_throughput", {
                            "queries_per_second": self.performance_stats["queries_per_second"],
                            "threshold": self.thresholds.low_throughput_ops_per_sec,
                            "total_queries": self.performance_stats["total_queries"]
                        })
                    
                except Exception as e:
                    logger.error(f"Monitoring collection error: {e}")
                
                time.sleep(collection_interval_seconds)
        
        self.collection_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.collection_thread.start()
        
        logger.info("Database performance monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        
        logger.info("Database performance monitoring stopped")
    
    def reset_statistics(self):
        """Reset performance statistics"""
        self.performance_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "failed_queries": 0,
            "avg_query_time": 0.0,
            "queries_per_second": 0.0,
            "last_reset": datetime.utcnow()
        }
        
        logger.info("Performance statistics reset")
    
    @contextmanager
    def monitor_operation(self, operation_name: str):
        """Context manager to monitor a specific operation"""
        start_time = time.time()
        
        try:
            yield
            execution_time = (time.time() - start_time) * 1000
            
            logger.info(f"Operation '{operation_name}' completed in {execution_time:.2f}ms")
            
            if execution_time > self.thresholds.slow_query_ms:
                self._trigger_alert("slow_operation", {
                    "operation_name": operation_name,
                    "execution_time_ms": execution_time,
                    "threshold": self.thresholds.slow_query_ms
                })
        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            logger.error(f"Operation '{operation_name}' failed after {execution_time:.2f}ms: {e}")
            
            self._trigger_alert("operation_failure", {
                "operation_name": operation_name,
                "execution_time_ms": execution_time,
                "error": str(e)
            })
            
            raise


# Global monitor instance
_performance_monitor: Optional[DatabasePerformanceMonitor] = None


def get_performance_monitor() -> DatabasePerformanceMonitor:
    """Get the global database performance monitor"""
    global _performance_monitor
    
    if _performance_monitor is None:
        _performance_monitor = DatabasePerformanceMonitor()
    
    return _performance_monitor


def initialize_monitoring(thresholds: Optional[PerformanceThresholds] = None,
                        start_collection: bool = True,
                        collection_interval: int = 30) -> DatabasePerformanceMonitor:
    """Initialize database performance monitoring"""
    global _performance_monitor
    
    _performance_monitor = DatabasePerformanceMonitor(thresholds)
    
    if start_collection:
        _performance_monitor.start_monitoring(collection_interval)
    
    logger.info("Database performance monitoring initialized")
    return _performance_monitor


def cleanup_monitoring():
    """Cleanup database performance monitoring"""
    global _performance_monitor
    
    if _performance_monitor:
        _performance_monitor.stop_monitoring()
        _performance_monitor = None
    
    logger.info("Database performance monitoring cleaned up")


# Decorator for monitoring database operations
def monitor_db_operation(operation_name: str):
    """Decorator to monitor database operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            
            with monitor.monitor_operation(operation_name):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Example alert handlers
def log_alert_handler(alert_type: str, alert_data: Dict[str, Any]):
    """Log alert handler - logs alerts to application log"""
    logger.warning(f"DB Performance Alert [{alert_type}]: {alert_data}")


def metrics_alert_handler(alert_type: str, alert_data: Dict[str, Any]):
    """Metrics alert handler - stores alerts as metrics"""
    try:
        with SessionLocal() as db:
            metric = PerformanceMetric(
                timestamp=datetime.utcnow(),
                metric_type="alert",
                metric_name=alert_type,
                value=1.0,
                unit="count",
                tags=str(alert_data)[:500]  # Truncate if too long
            )
            db.add(metric)
            db.commit()
    except Exception as e:
        logger.error(f"Failed to store alert metric: {e}")
