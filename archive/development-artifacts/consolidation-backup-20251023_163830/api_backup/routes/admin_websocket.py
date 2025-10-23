"""
WebSocket Administration Routes for T025 Phase 4
Admin endpoints for monitoring and managing WebSocket connections and performance.
"""

from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from api.orm_bootstrap import get_db
from api.services.enhanced_websocket_service import get_websocket_service, EnhancedWebSocketService
from api.routes.auth import verify_token
from api.models import User
from api.utils.logger import get_system_logger

logger = get_system_logger("admin_websocket")

# Simple admin role check (replace with proper auth when available)
async def requires_admin_role(token: str = Depends(verify_token)):
    """Require admin role for access."""
    # This is a simplified check - in production use proper user role verification
    return token  # For now, just require valid token

router = APIRouter(
    prefix="/admin/websocket",
    tags=["admin", "websocket", "monitoring"],
    dependencies=[Depends(requires_admin_role)]
)

@router.get("/status", response_model=Dict[str, Any])
async def get_websocket_status():
    """Get current WebSocket service status and metrics."""
    try:
        websocket_service = await get_websocket_service()
        
        metrics = websocket_service.get_metrics()
        connection_status = websocket_service.get_connection_status()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "service_status": {
                "is_running": websocket_service.is_running,
                "redis_connected": websocket_service.message_queue.redis_client is not None,
                "subscriber_running": websocket_service.message_queue.running,
                "cleanup_task_running": websocket_service.connection_pool.cleanup_task is not None and not websocket_service.connection_pool.cleanup_task.done()
            },
            "connection_metrics": metrics,
            "connection_status": connection_status,
            "health_assessment": _assess_websocket_health(metrics, connection_status)
        }
        
    except Exception as e:
        logger.error(f"Failed to get WebSocket status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get WebSocket status: {str(e)}")

@router.get("/connections", response_model=Dict[str, Any])
async def get_active_connections():
    """Get detailed information about active WebSocket connections."""
    try:
        websocket_service = await get_websocket_service()
        
        connections_info = []
        for connection_id, conn_info in websocket_service.connection_pool.connections.items():
            connections_info.append({
                "connection_id": connection_id,
                "user_id": conn_info.user_id,
                "job_id": conn_info.job_id,
                "connected_at": conn_info.connected_at.isoformat(),
                "last_activity": conn_info.last_activity.isoformat(),
                "subscriptions": list(conn_info.subscriptions),
                "connection_age_minutes": (datetime.utcnow() - conn_info.connected_at).total_seconds() / 60,
                "idle_minutes": (datetime.utcnow() - conn_info.last_activity).total_seconds() / 60
            })
        
        # Sort by connection age (newest first)
        connections_info.sort(key=lambda x: x["connected_at"], reverse=True)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_connections": len(connections_info),
            "connections": connections_info[:50],  # Limit to first 50 for performance
            "has_more": len(connections_info) > 50
        }
        
    except Exception as e:
        logger.error(f"Failed to get active connections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active connections: {str(e)}")

@router.get("/metrics/detailed", response_model=Dict[str, Any])
async def get_detailed_metrics():
    """Get detailed WebSocket performance metrics."""
    try:
        websocket_service = await get_websocket_service()
        
        metrics = websocket_service.get_metrics()
        connection_status = websocket_service.get_connection_status()
        
        # Calculate additional metrics
        pool_metrics = websocket_service.connection_pool.metrics
        
        # Connection distribution analysis
        job_distribution = {}
        user_distribution = {}
        
        for job_id, connection_ids in websocket_service.connection_pool.job_connections.items():
            job_distribution[job_id] = len(connection_ids)
        
        for user_id, connection_ids in websocket_service.connection_pool.user_connections.items():
            user_distribution[str(user_id)] = len(connection_ids)
        
        # Performance analysis
        performance_analysis = {
            "average_connections_per_job": len(job_distribution) / max(len(websocket_service.connection_pool.job_connections), 1),
            "average_connections_per_user": len(user_distribution) / max(len(websocket_service.connection_pool.user_connections), 1),
            "message_rate_per_minute": pool_metrics.messages_sent / max((datetime.utcnow() - pool_metrics.last_reset).total_seconds() / 60, 1),
            "error_rate_percent": (pool_metrics.connection_errors / max(pool_metrics.total_connects, 1)) * 100,
            "connection_success_rate": ((pool_metrics.total_connects - pool_metrics.connection_errors) / max(pool_metrics.total_connects, 1)) * 100
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "basic_metrics": metrics,
            "connection_distribution": {
                "by_job": job_distribution,
                "by_user": user_distribution
            },
            "performance_analysis": performance_analysis,
            "recommendations": _generate_websocket_recommendations(metrics, connection_status, performance_analysis)
        }
        
    except Exception as e:
        logger.error(f"Failed to get detailed metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get detailed metrics: {str(e)}")

@router.post("/broadcast", response_model=Dict[str, Any])
async def admin_broadcast_message(
    message: str,
    broadcast_type: str = "info",
    target_users: List[int] = None,
    target_jobs: List[str] = None
):
    """Send broadcast messages to WebSocket connections."""
    try:
        websocket_service = await get_websocket_service()
        
        sent_count = 0
        
        if target_users:
            # Send to specific users
            for user_id in target_users:
                count = await websocket_service.connection_pool.broadcast_to_user(user_id, {
                    "type": "admin_message",
                    "broadcast_type": broadcast_type,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                })
                sent_count += count
                
        elif target_jobs:
            # Send to specific jobs
            for job_id in target_jobs:
                count = await websocket_service.connection_pool.broadcast_to_job(job_id, {
                    "type": "admin_message",
                    "broadcast_type": broadcast_type,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                })
                sent_count += count
                
        else:
            # Broadcast to all connections
            sent_count = await websocket_service.connection_pool.broadcast_to_all({
                "type": "admin_broadcast",
                "broadcast_type": broadcast_type,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return {
            "status": "success",
            "message": "Broadcast sent successfully",
            "sent_to_connections": sent_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send broadcast: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send broadcast: {str(e)}")

@router.post("/connections/{connection_id}/disconnect", response_model=Dict[str, Any])
async def disconnect_connection(connection_id: str):
    """Forcibly disconnect a specific WebSocket connection."""
    try:
        websocket_service = await get_websocket_service()
        
        conn_info = websocket_service.connection_pool.get_connection_info(connection_id)
        if not conn_info:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Close the WebSocket connection
        await conn_info.websocket.close(code=1008, reason="Admin disconnect")
        await websocket_service.disconnect_websocket(connection_id)
        
        return {
            "status": "success",
            "message": f"Connection {connection_id} disconnected successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect connection {connection_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disconnect connection: {str(e)}")

@router.post("/maintenance/cleanup", response_model=Dict[str, Any])
async def trigger_cleanup(background_tasks: BackgroundTasks):
    """Trigger manual cleanup of stale WebSocket connections."""
    try:
        websocket_service = await get_websocket_service()
        
        # Get current connection count
        initial_count = len(websocket_service.connection_pool.connections)
        
        # Run cleanup in background
        background_tasks.add_task(_perform_websocket_cleanup, websocket_service)
        
        return {
            "status": "cleanup_scheduled",
            "message": "WebSocket cleanup scheduled in background",
            "initial_connection_count": initial_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger cleanup: {str(e)}")

@router.get("/health", response_model=Dict[str, Any])
async def get_websocket_health():
    """Get WebSocket service health assessment."""
    try:
        websocket_service = await get_websocket_service()
        
        metrics = websocket_service.get_metrics()
        connection_status = websocket_service.get_connection_status()
        
        health_assessment = _assess_websocket_health(metrics, connection_status)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health_score": health_assessment["score"],
            "status": health_assessment["status"],
            "issues": health_assessment["issues"],
            "recommendations": health_assessment["recommendations"],
            "metrics_summary": {
                "active_connections": connection_status["total_connections"],
                "utilization_percent": connection_status["utilization_percent"],
                "error_rate": metrics["connection_pool"]["connection_errors"],
                "message_throughput": metrics["messaging"]["messages_sent"]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get WebSocket health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get WebSocket health: {str(e)}")

@router.get("/performance/analysis", response_model=Dict[str, Any])
async def get_performance_analysis():
    """Get detailed WebSocket performance analysis."""
    try:
        websocket_service = await get_websocket_service()
        
        metrics = websocket_service.get_metrics()
        connection_status = websocket_service.get_connection_status()
        
        # Performance trend analysis
        pool_metrics = websocket_service.connection_pool.metrics
        
        analysis = {
            "connection_performance": {
                "peak_connections": pool_metrics.peak_connections,
                "current_utilization": connection_status["utilization_percent"],
                "connection_success_rate": ((pool_metrics.total_connects - pool_metrics.connection_errors) / max(pool_metrics.total_connects, 1)) * 100,
                "average_connection_lifetime": "N/A"  # Would need historical data
            },
            "message_performance": {
                "total_messages": pool_metrics.messages_sent,
                "average_message_time_ms": pool_metrics.average_message_time_ms,
                "message_types_distribution": pool_metrics.message_types,
                "throughput_assessment": "normal" if pool_metrics.average_message_time_ms < 100 else "slow"
            },
            "resource_utilization": {
                "redis_connected": websocket_service.message_queue.redis_client is not None,
                "cleanup_active": websocket_service.connection_pool.cleanup_task is not None,
                "memory_connections": len(websocket_service.connection_pool.connections),
                "job_mappings": len(websocket_service.connection_pool.job_connections),
                "user_mappings": len(websocket_service.connection_pool.user_connections)
            },
            "optimization_opportunities": _identify_optimization_opportunities(metrics, connection_status)
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis": analysis,
            "performance_grade": _calculate_websocket_performance_grade(analysis)
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance analysis: {str(e)}")

# Helper functions

async def _perform_websocket_cleanup(websocket_service: EnhancedWebSocketService):
    """Background task to perform WebSocket cleanup."""
    try:
        logger.info("Starting manual WebSocket cleanup")
        
        initial_count = len(websocket_service.connection_pool.connections)
        await websocket_service.connection_pool.cleanup_stale_connections(max_idle_minutes=15)
        final_count = len(websocket_service.connection_pool.connections)
        
        cleaned_count = initial_count - final_count
        logger.info(f"WebSocket cleanup completed: cleaned {cleaned_count} connections")
        
    except Exception as e:
        logger.error(f"WebSocket cleanup task failed: {e}")

def _assess_websocket_health(metrics: Dict[str, Any], connection_status: Dict[str, Any]) -> Dict[str, Any]:
    """Assess the health of the WebSocket service."""
    issues = []
    recommendations = []
    score = 100
    
    # Check utilization
    utilization = connection_status.get("utilization_percent", 0)
    if utilization > 90:
        issues.append("High connection pool utilization")
        recommendations.append("Consider increasing max_connections")
        score -= 20
    elif utilization > 70:
        issues.append("Moderate connection pool utilization")
        score -= 10
    
    # Check error rate
    error_count = metrics.get("connection_pool", {}).get("connection_errors", 0)
    total_connects = metrics.get("connection_pool", {}).get("total_connects", 1)
    error_rate = (error_count / total_connects) * 100
    
    if error_rate > 10:
        issues.append(f"High connection error rate: {error_rate:.1f}%")
        recommendations.append("Investigate connection failures")
        score -= 25
    elif error_rate > 5:
        issues.append(f"Moderate connection error rate: {error_rate:.1f}%")
        score -= 10
    
    # Check message performance
    avg_message_time = metrics.get("messaging", {}).get("average_message_time_ms", 0)
    if avg_message_time > 200:
        issues.append(f"Slow message delivery: {avg_message_time:.1f}ms average")
        recommendations.append("Investigate message delivery performance")
        score -= 15
    
    # Check service status
    service_status = metrics.get("service_status", {})
    if not service_status.get("redis_connected", False):
        issues.append("Redis connection lost")
        recommendations.append("Check Redis server status")
        score -= 30
    
    # Determine overall status
    if score >= 80:
        status = "healthy"
    elif score >= 60:
        status = "warning"
    else:
        status = "critical"
    
    return {
        "score": max(0, score),
        "status": status,
        "issues": issues,
        "recommendations": recommendations
    }

def _generate_websocket_recommendations(metrics: Dict[str, Any], connection_status: Dict[str, Any], 
                                      performance_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate optimization recommendations for WebSocket service."""
    recommendations = []
    
    # Connection pool recommendations
    utilization = connection_status.get("utilization_percent", 0)
    if utilization > 80:
        recommendations.append({
            "type": "capacity",
            "priority": "high",
            "issue": "High connection pool utilization",
            "suggestion": "Increase max_connections or implement connection pooling optimization"
        })
    
    # Message performance recommendations
    avg_time = metrics.get("messaging", {}).get("average_message_time_ms", 0)
    if avg_time > 100:
        recommendations.append({
            "type": "performance",
            "priority": "medium",
            "issue": f"Message delivery time above threshold: {avg_time:.1f}ms",
            "suggestion": "Optimize message serialization or Redis connection"
        })
    
    # Connection distribution recommendations
    if performance_analysis.get("average_connections_per_user", 0) > 5:
        recommendations.append({
            "type": "optimization",
            "priority": "low",
            "issue": "High connections per user ratio",
            "suggestion": "Consider implementing connection sharing or rate limiting"
        })
    
    if not recommendations:
        recommendations.append({
            "type": "status",
            "priority": "info",
            "issue": "No issues detected",
            "suggestion": "WebSocket service is operating optimally"
        })
    
    return recommendations

def _identify_optimization_opportunities(metrics: Dict[str, Any], connection_status: Dict[str, Any]) -> List[str]:
    """Identify specific optimization opportunities."""
    opportunities = []
    
    # Check for connection pooling optimization
    if connection_status.get("utilization_percent", 0) > 70:
        opportunities.append("Implement connection pooling with better resource allocation")
    
    # Check for message batching opportunities
    message_count = metrics.get("messaging", {}).get("messages_sent", 0)
    if message_count > 1000:  # High message volume
        opportunities.append("Consider implementing message batching for high-frequency updates")
    
    # Check for Redis optimization
    if metrics.get("service_status", {}).get("redis_connected", False):
        opportunities.append("Optimize Redis pub/sub channels for better message distribution")
    
    # Check for cleanup optimization
    active_connections = connection_status.get("total_connections", 0)
    if active_connections > 100:
        opportunities.append("Implement more aggressive connection cleanup for better resource management")
    
    return opportunities if opportunities else ["No specific optimization opportunities identified"]

def _calculate_websocket_performance_grade(analysis: Dict[str, Any]) -> str:
    """Calculate a performance grade for the WebSocket service."""
    try:
        score = 100
        
        # Connection performance impact
        success_rate = analysis.get("connection_performance", {}).get("connection_success_rate", 100)
        if success_rate < 95:
            score -= 20
        elif success_rate < 98:
            score -= 10
        
        # Message performance impact
        avg_time = analysis.get("message_performance", {}).get("average_message_time_ms", 0)
        if avg_time > 200:
            score -= 25
        elif avg_time > 100:
            score -= 15
        elif avg_time > 50:
            score -= 5
        
        # Resource utilization impact
        resource_util = analysis.get("resource_utilization", {})
        if not resource_util.get("redis_connected", False):
            score -= 30
        
        # Assign grade
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        else:
            return "D"
            
    except Exception:
        return "N/A"
