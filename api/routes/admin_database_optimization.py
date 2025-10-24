"""
Database Optimization Admin Routes
Administrative endpoints for monitoring and managing database optimization.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from api.orm_bootstrap import get_db
from api.services.database_optimization_integration import get_optimization_service, DatabaseOptimizationService
from api.database_performance_monitor import get_performance_monitor, PerformanceThresholds
from api.routes.auth import verify_token
from api.models import User
from api.utils.logger import get_system_logger

logger = get_system_logger("admin_database")

# Simple admin role check (replace with proper auth when available)
async def requires_admin_role(token: str = Depends(verify_token)):
    """Require admin role for access."""
    # This is a simplified check - in production use proper user role verification
    return token  # For now, just require valid token

router = APIRouter(
    prefix="/admin/database",
    tags=["admin", "database", "optimization"],
    dependencies=[Depends(requires_admin_role)]
)

@router.get("/optimization/status", response_model=Dict[str, Any])
async def get_optimization_status():
    """Get current database optimization status and performance metrics."""
    try:
        optimization_service = await get_optimization_service()
        performance_monitor = get_performance_monitor()
        
        # Get performance analysis
        performance_data = await optimization_service.get_performance_analysis()
        
        # Get connection pool status
        if optimization_service.optimizer:
            pool_status = await optimization_service.optimizer.get_connection_pool_status()
        else:
            pool_status = {"status": "optimizer_not_available"}
        
        # Get real-time monitoring data
        monitoring_summary = performance_monitor.get_performance_summary(60)  # Last 60 minutes
        
        return {
            "status": "active" if optimization_service.optimizer else "not_initialized",
            "timestamp": datetime.utcnow().isoformat(),
            "performance_analysis": performance_data,
            "connection_pool": pool_status,
            "real_time_monitoring": monitoring_summary,
            "monitoring_active": performance_monitor.monitoring_active,
            "optimization_features": {
                "enhanced_connection_pooling": optimization_service.optimizer is not None,
                "query_performance_monitoring": True,
                "advanced_query_patterns": True,
                "cache_integration": True,
                "maintenance_automation": True
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get optimization status: {str(e)}")

@router.get("/performance/analysis", response_model=Dict[str, Any])
async def get_performance_analysis():
    """Get detailed database performance analysis."""
    try:
        optimization_service = await get_optimization_service()
        analysis = await optimization_service.get_performance_analysis()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis": analysis,
            "recommendations": await _generate_performance_recommendations(analysis)
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Performance analysis failed: {str(e)}")

@router.get("/health", response_model=Dict[str, Any])
async def get_database_health():
    """Get comprehensive database health metrics."""
    try:
        optimization_service = await get_optimization_service()
        health_data = await optimization_service.get_system_health()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health": health_data,
            "optimization_impact": await _calculate_optimization_impact(optimization_service)
        }
        
    except Exception as e:
        logger.error(f"Failed to get database health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/maintenance/run", response_model=Dict[str, Any])
async def run_database_maintenance(background_tasks: BackgroundTasks):
    """Trigger database maintenance operations."""
    try:
        optimization_service = await get_optimization_service()
        
        # Run maintenance in background
        background_tasks.add_task(_perform_maintenance_task, optimization_service)
        
        return {
            "status": "maintenance_scheduled",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Database maintenance operations scheduled in background"
        }
        
    except Exception as e:
        logger.error(f"Failed to schedule maintenance: {e}")
        raise HTTPException(status_code=500, detail=f"Maintenance scheduling failed: {str(e)}")

@router.get("/queries/slow", response_model=Dict[str, Any])
async def get_slow_queries():
    """Get information about slow queries and optimization opportunities."""
    try:
        optimization_service = await get_optimization_service()
        
        if not optimization_service.optimizer:
            return {"message": "Query monitoring not available"}
        
        performance_data = await optimization_service.get_performance_analysis()
        
        # Extract slow query information
        slow_queries = performance_data.get("slow_queries", [])
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "slow_queries": slow_queries,
            "total_slow_queries": len(slow_queries),
            "optimization_suggestions": await _generate_query_optimization_suggestions(slow_queries)
        }
        
    except Exception as e:
        logger.error(f"Failed to get slow queries: {e}")
        raise HTTPException(status_code=500, detail=f"Slow query analysis failed: {str(e)}")

@router.get("/connection-pool/stats", response_model=Dict[str, Any])
async def get_connection_pool_stats():
    """Get detailed connection pool statistics."""
    try:
        optimization_service = await get_optimization_service()
        
        if not optimization_service.optimizer:
            return {"message": "Connection pool monitoring not available"}
        
        pool_status = await optimization_service.optimizer.get_connection_pool_status()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "pool_statistics": pool_status,
            "health_assessment": _assess_pool_health(pool_status)
        }
        
    except Exception as e:
        logger.error(f"Failed to get connection pool stats: {e}")
        raise HTTPException(status_code=500, detail=f"Connection pool stats failed: {str(e)}")

@router.post("/optimization/enable", response_model=Dict[str, Any])
async def enable_optimization():
    """Enable advanced database optimization features."""
    try:
        optimization_service = await get_optimization_service()
        
        if optimization_service.optimizer:
            return {
                "status": "already_enabled",
                "message": "Database optimization is already active"
            }
        
        # Reinitialize optimization service
        await optimization_service.initialize()
        
        return {
            "status": "enabled",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Database optimization features enabled successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to enable optimization: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enable optimization: {str(e)}")

@router.get("/metrics/summary", response_model=Dict[str, Any])
async def get_optimization_metrics_summary():
    """Get a summary of key optimization metrics."""
    try:
        optimization_service = await get_optimization_service()
        
        if not optimization_service.optimizer:
            return {"message": "Optimization metrics not available"}
        
        stats = optimization_service.optimizer.performance_stats
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "total_queries": stats.get("total_queries", 0),
                "slow_queries": stats.get("slow_queries", 0),
                "cache_hits": stats.get("cache_hits", 0),
                "average_query_time_ms": stats.get("avg_query_time", 0) * 1000,
                "slow_query_percentage": (
                    (stats.get("slow_queries", 0) / max(stats.get("total_queries", 1), 1)) * 100
                ),
                "last_optimization": stats.get("last_optimization")
            },
            "performance_grade": _calculate_performance_grade(stats)
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")

# Helper functions

async def _generate_performance_recommendations(analysis: Dict[str, Any]) -> list:
    """Generate performance recommendations based on analysis."""
    recommendations = []
    
    try:
        slow_queries = analysis.get("slow_queries", [])
        table_patterns = analysis.get("table_access_patterns", [])
        
        # Analyze slow queries
        if len(slow_queries) > 0:
            if any(q.get("avg_time_ms", 0) > 500 for q in slow_queries):
                recommendations.append({
                    "type": "query_optimization",
                    "priority": "high",
                    "issue": "Very slow queries detected (>500ms)",
                    "suggestion": "Review query structure and consider adding indexes"
                })
            
            select_heavy = [q for q in slow_queries if q.get("query_type") == "SELECT"]
            if len(select_heavy) > len(slow_queries) * 0.7:
                recommendations.append({
                    "type": "indexing",
                    "priority": "medium",
                    "issue": "High proportion of slow SELECT queries",
                    "suggestion": "Consider adding covering indexes for frequently accessed columns"
                })
        
        # Analyze table access patterns
        if len(table_patterns) > 0:
            high_access_tables = [t for t in table_patterns if t.get("access_count", 0) > 100]
            if high_access_tables:
                recommendations.append({
                    "type": "caching",
                    "priority": "medium",
                    "issue": f"High access frequency on tables: {[t['table'] for t in high_access_tables]}",
                    "suggestion": "Consider implementing query result caching for frequently accessed data"
                })
        
        if not recommendations:
            recommendations.append({
                "type": "general",
                "priority": "low",
                "issue": "No major performance issues detected",
                "suggestion": "Continue monitoring performance metrics"
            })
    
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {e}")
        recommendations.append({
            "type": "error",
            "priority": "high",
            "issue": "Failed to analyze performance data",
            "suggestion": "Check system logs for detailed error information"
        })
    
    return recommendations

async def _calculate_optimization_impact(optimization_service) -> Dict[str, Any]:
    """Calculate the impact of optimization features."""
    try:
        if not optimization_service.optimizer:
            return {"status": "no_optimizer"}
        
        stats = optimization_service.optimizer.performance_stats
        
        total_queries = stats.get("total_queries", 0)
        slow_queries = stats.get("slow_queries", 0)
        cache_hits = stats.get("cache_hits", 0)
        
        return {
            "query_performance_improvement": max(0, 100 - (slow_queries / max(total_queries, 1) * 100)),
            "cache_efficiency": (cache_hits / max(total_queries, 1) * 100) if total_queries > 0 else 0,
            "average_response_time_ms": stats.get("avg_query_time", 0) * 1000,
            "optimization_effectiveness": "high" if slow_queries / max(total_queries, 1) < 0.05 else "medium" if slow_queries / max(total_queries, 1) < 0.15 else "low"
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate optimization impact: {e}")
        return {"error": str(e)}

async def _perform_maintenance_task(optimization_service):
    """Background task to perform database maintenance."""
    try:
        logger.info("Starting scheduled database maintenance")
        success = await optimization_service.perform_maintenance()
        
        if success:
            logger.info("Database maintenance completed successfully")
        else:
            logger.warning("Database maintenance completed with warnings")
            
    except Exception as e:
        logger.error(f"Database maintenance task failed: {e}")

async def _generate_query_optimization_suggestions(slow_queries: list) -> list:
    """Generate specific optimization suggestions for slow queries."""
    suggestions = []
    
    try:
        for query in slow_queries[:5]:  # Top 5 slow queries
            query_type = query.get("query_type", "unknown")
            table_name = query.get("table", "unknown")
            avg_time = query.get("avg_time_ms", 0)
            
            if avg_time > 1000:  # Very slow (>1s)
                suggestions.append({
                    "query_type": query_type,
                    "table": table_name,
                    "current_avg_time_ms": avg_time,
                    "suggestion": f"Critical: {query_type} on {table_name} averaging {avg_time:.0f}ms - needs immediate optimization",
                    "recommended_actions": [
                        "Review query execution plan",
                        "Add appropriate indexes",
                        "Consider query restructuring"
                    ]
                })
            elif avg_time > 500:  # Moderately slow (>500ms)
                suggestions.append({
                    "query_type": query_type,
                    "table": table_name,
                    "current_avg_time_ms": avg_time,
                    "suggestion": f"Moderate: {query_type} on {table_name} could be optimized",
                    "recommended_actions": [
                        "Check for missing indexes",
                        "Analyze query patterns"
                    ]
                })
    
    except Exception as e:
        logger.error(f"Failed to generate query suggestions: {e}")
    
    return suggestions

def _assess_pool_health(pool_status: Dict[str, Any]) -> Dict[str, Any]:
    """Assess the health of the connection pool."""
    try:
        if pool_status.get("status") == "not_initialized":
            return {"status": "not_available", "message": "Connection pool not initialized"}
        
        utilization = pool_status.get("utilization_percent", 0)
        
        if utilization > 90:
            health = "critical"
            message = "Connection pool near capacity - consider increasing pool size"
        elif utilization > 70:
            health = "warning"
            message = "High connection pool utilization"
        else:
            health = "healthy"
            message = "Connection pool operating normally"
        
        return {
            "status": health,
            "utilization_percent": utilization,
            "message": message,
            "recommendations": _get_pool_recommendations(pool_status)
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

def _get_pool_recommendations(pool_status: Dict[str, Any]) -> list:
    """Get recommendations for connection pool optimization."""
    recommendations = []
    
    try:
        utilization = pool_status.get("utilization_percent", 0)
        overflow = pool_status.get("overflow", 0)
        
        if utilization > 80:
            recommendations.append("Consider increasing base pool size")
        
        if overflow > 0:
            recommendations.append("Overflow connections being used - monitor for connection leaks")
        
        if not recommendations:
            recommendations.append("Connection pool is optimally configured")
    
    except Exception as e:
        recommendations.append(f"Error generating recommendations: {e}")
    
    return recommendations

def _calculate_performance_grade(stats: Dict[str, Any]) -> str:
    """Calculate a performance grade based on statistics."""
    try:
        total_queries = stats.get("total_queries", 0)
        slow_queries = stats.get("slow_queries", 0)
        avg_query_time = stats.get("avg_query_time", 0)
        
        if total_queries == 0:
            return "N/A"
        
        slow_query_rate = slow_queries / total_queries
        avg_time_ms = avg_query_time * 1000
        
        # Grade based on slow query rate and average time
        if slow_query_rate < 0.02 and avg_time_ms < 50:
            return "A+"
        elif slow_query_rate < 0.05 and avg_time_ms < 100:
            return "A"
        elif slow_query_rate < 0.10 and avg_time_ms < 200:
            return "B"
        elif slow_query_rate < 0.20 and avg_time_ms < 500:
            return "C"
        else:
            return "D"
            
    except Exception as e:
        logger.error(f"Failed to calculate performance grade: {e}")
        return "Error"


# Enhanced monitoring endpoints

@router.get("/monitoring/summary", response_model=Dict[str, Any])
async def get_monitoring_summary(minutes: int = Query(60, ge=1, le=1440)):
    """Get real-time database performance monitoring summary."""
    try:
        performance_monitor = get_performance_monitor()
        
        summary = performance_monitor.get_performance_summary(minutes)
        
        return {
            "status": "success",
            "monitoring_summary": summary,
            "monitoring_active": performance_monitor.monitoring_active,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get monitoring summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring summary: {str(e)}")


@router.get("/monitoring/slow-queries", response_model=Dict[str, Any])
async def get_realtime_slow_queries(limit: int = Query(10, ge=1, le=100), minutes: int = Query(60, ge=1, le=1440)):
    """Get top slow queries from recent monitoring data."""
    try:
        performance_monitor = get_performance_monitor()
        
        slow_queries = performance_monitor.get_top_slow_queries(limit, minutes)
        
        return {
            "status": "success",
            "slow_queries": slow_queries,
            "period_minutes": minutes,
            "limit": limit,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get slow queries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get slow queries: {str(e)}")


@router.post("/monitoring/start", response_model=Dict[str, Any])
async def start_monitoring(interval_seconds: int = Query(30, ge=10, le=300)):
    """Start database performance monitoring."""
    try:
        performance_monitor = get_performance_monitor()
        
        if performance_monitor.monitoring_active:
            return {
                "status": "already_running",
                "message": "Database monitoring is already active",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        performance_monitor.start_monitoring(interval_seconds)
        
        return {
            "status": "started",
            "message": f"Database monitoring started with {interval_seconds}s interval",
            "interval_seconds": interval_seconds,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")


@router.post("/monitoring/stop", response_model=Dict[str, Any])
async def stop_monitoring():
    """Stop database performance monitoring."""
    try:
        performance_monitor = get_performance_monitor()
        
        if not performance_monitor.monitoring_active:
            return {
                "status": "already_stopped",
                "message": "Database monitoring is not currently active",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        performance_monitor.stop_monitoring()
        
        return {
            "status": "stopped",
            "message": "Database monitoring stopped",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")


@router.post("/monitoring/reset", response_model=Dict[str, Any])
async def reset_monitoring_statistics():
    """Reset database performance monitoring statistics."""
    try:
        performance_monitor = get_performance_monitor()
        
        performance_monitor.reset_statistics()
        
        return {
            "status": "reset",
            "message": "Database monitoring statistics reset",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reset monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset monitoring: {str(e)}")


@router.get("/monitoring/thresholds", response_model=Dict[str, Any])
async def get_monitoring_thresholds():
    """Get current performance monitoring thresholds."""
    try:
        performance_monitor = get_performance_monitor()
        
        return {
            "status": "success",
            "thresholds": {
                "slow_query_ms": performance_monitor.thresholds.slow_query_ms,
                "very_slow_query_ms": performance_monitor.thresholds.very_slow_query_ms,
                "connection_timeout_ms": performance_monitor.thresholds.connection_timeout_ms,
                "high_cpu_percentage": performance_monitor.thresholds.high_cpu_percentage,
                "low_throughput_ops_per_sec": performance_monitor.thresholds.low_throughput_ops_per_sec,
                "high_error_rate_percentage": performance_monitor.thresholds.high_error_rate_percentage
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get thresholds: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get thresholds: {str(e)}")


@router.put("/monitoring/thresholds", response_model=Dict[str, Any])
async def update_monitoring_thresholds(
    slow_query_ms: Optional[float] = Query(None, ge=10, le=10000),
    very_slow_query_ms: Optional[float] = Query(None, ge=100, le=30000),
    high_error_rate_percentage: Optional[float] = Query(None, ge=0.1, le=50.0),
    low_throughput_ops_per_sec: Optional[float] = Query(None, ge=0.1, le=1000.0)
):
    """Update performance monitoring thresholds."""
    try:
        performance_monitor = get_performance_monitor()
        
        updated_fields = []
        
        if slow_query_ms is not None:
            performance_monitor.thresholds.slow_query_ms = slow_query_ms
            updated_fields.append(f"slow_query_ms: {slow_query_ms}")
        
        if very_slow_query_ms is not None:
            performance_monitor.thresholds.very_slow_query_ms = very_slow_query_ms
            updated_fields.append(f"very_slow_query_ms: {very_slow_query_ms}")
        
        if high_error_rate_percentage is not None:
            performance_monitor.thresholds.high_error_rate_percentage = high_error_rate_percentage
            updated_fields.append(f"high_error_rate_percentage: {high_error_rate_percentage}")
        
        if low_throughput_ops_per_sec is not None:
            performance_monitor.thresholds.low_throughput_ops_per_sec = low_throughput_ops_per_sec
            updated_fields.append(f"low_throughput_ops_per_sec: {low_throughput_ops_per_sec}")
        
        return {
            "status": "updated",
            "message": f"Updated thresholds: {', '.join(updated_fields)}",
            "updated_thresholds": {
                "slow_query_ms": performance_monitor.thresholds.slow_query_ms,
                "very_slow_query_ms": performance_monitor.thresholds.very_slow_query_ms,
                "high_error_rate_percentage": performance_monitor.thresholds.high_error_rate_percentage,
                "low_throughput_ops_per_sec": performance_monitor.thresholds.low_throughput_ops_per_sec
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update thresholds: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update thresholds: {str(e)}")
