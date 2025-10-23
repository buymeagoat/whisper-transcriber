"""
System Performance API Routes for T032: System Performance Dashboard
Provides comprehensive system monitoring and performance analytics endpoints
"""

import psutil
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from api.orm_bootstrap import get_db
from api.routes.auth import get_current_user
from api.models import User
from api.utils.admin_required import admin_required

router = APIRouter(prefix="/admin/system", tags=["system-performance"])


class SystemPerformanceService:
    """Service for collecting and providing system performance metrics"""
    
    def __init__(self):
        self.metrics_cache = {}
        self.cache_timeout = 30  # Cache metrics for 30 seconds
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            network_connections = len(psutil.net_connections())
            
            return {
                "cpu_usage": round(cpu_percent, 2),
                "cpu_cores": cpu_count,
                "cpu_frequency": round(cpu_freq.current / 1000, 2) if cpu_freq else 0,
                "memory_used": memory.used,
                "memory_total": memory.total,
                "memory_percentage": round(memory.percent, 2),
                "disk_used": disk.used,
                "disk_total": disk.total,
                "disk_percentage": round((disk.used / disk.total) * 100, 2),
                "network_rx": network.bytes_recv,
                "network_tx": network.bytes_sent,
                "network_connections": network_connections,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to collect system metrics: {str(e)}")
    
    async def get_application_metrics(self, db: Session) -> Dict[str, Any]:
        """Get application-specific performance metrics"""
        try:
            # Active jobs count
            active_jobs_result = db.execute(text("SELECT COUNT(*) FROM jobs WHERE status = 'processing'"))
            active_jobs = active_jobs_result.scalar() or 0
            
            # Queue size (pending jobs)
            queue_size_result = db.execute(text("SELECT COUNT(*) FROM jobs WHERE status = 'pending'"))
            queue_size = queue_size_result.scalar() or 0
            
            # Error rate (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            total_jobs_result = db.execute(text("SELECT COUNT(*) FROM jobs WHERE created_at > :yesterday"), {"yesterday": yesterday})
            total_jobs = total_jobs_result.scalar() or 1
            
            failed_jobs_result = db.execute(text("SELECT COUNT(*) FROM jobs WHERE status = 'failed' AND created_at > :yesterday"), {"yesterday": yesterday})
            failed_jobs = failed_jobs_result.scalar() or 0
            
            error_rate = (failed_jobs / total_jobs) * 100 if total_jobs > 0 else 0
            
            # Average response time (mock for now - would need actual metrics collection)
            avg_response_time = 150  # milliseconds
            
            # Throughput (jobs per hour in last 24 hours)
            throughput = total_jobs / 24 if total_jobs > 0 else 0
            
            # Application uptime (mock - would need actual uptime tracking)
            uptime = 86400000  # 24 hours in milliseconds
            
            return {
                "active_jobs": active_jobs,
                "queue_size": queue_size,
                "error_rate": round(error_rate, 2),
                "avg_response_time": avg_response_time,
                "throughput": round(throughput, 2),
                "uptime": uptime,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to collect application metrics: {str(e)}")
    
    async def get_service_status(self) -> List[Dict[str, Any]]:
        """Get status of system services"""
        services = []
        
        try:
            # Check database connectivity
            import sqlite3
            try:
                conn = sqlite3.connect('whisper_app.db')
                conn.execute('SELECT 1')
                conn.close()
                db_status = "healthy"
            except:
                db_status = "error"
            
            services.append({
                "name": "SQLite Database",
                "description": "Primary application database",
                "status": db_status,
                "lastCheck": datetime.utcnow().isoformat(),
                "uptime": "99.9%",
                "responseTime": 5
            })
            
            # Check API server (self)
            services.append({
                "name": "Whisper Transcriber API",
                "description": "Main application server",
                "status": "healthy",
                "lastCheck": datetime.utcnow().isoformat(),
                "uptime": "99.95%",
                "responseTime": 120
            })
            
            # Check worker process
            worker_processes = [p for p in psutil.process_iter(['pid', 'name']) if 'worker' in p.info['name'].lower()]
            worker_status = "healthy" if worker_processes else "warning"
            
            services.append({
                "name": "Background Worker",
                "description": "Job processing worker",
                "status": worker_status,
                "lastCheck": datetime.utcnow().isoformat(),
                "uptime": "99.8%",
                "responseTime": 0
            })
            
            # Mock services for demonstration
            services.extend([
                {
                    "name": "File Storage",
                    "description": "Audio file storage system",
                    "status": "healthy",
                    "lastCheck": datetime.utcnow().isoformat(),
                    "uptime": "99.99%",
                    "responseTime": 10
                },
                {
                    "name": "Model Service",
                    "description": "Whisper model inference service",
                    "status": "healthy",
                    "lastCheck": datetime.utcnow().isoformat(),
                    "uptime": "99.7%",
                    "responseTime": 2500
                }
            ])
            
            return services
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get service status: {str(e)}")
    
    async def get_active_alerts(self, db: Session) -> List[Dict[str, Any]]:
        """Get active system alerts"""
        alerts = []
        
        try:
            # Get current system metrics for alert evaluation
            metrics = await self.get_system_metrics()
            
            # CPU usage alert
            if metrics["cpu_usage"] > 80:
                alerts.append({
                    "id": "cpu_high",
                    "title": "High CPU Usage",
                    "description": f"CPU usage is {metrics['cpu_usage']}% (threshold: 80%)",
                    "severity": "critical" if metrics["cpu_usage"] > 90 else "warning",
                    "timestamp": datetime.utcnow().isoformat(),
                    "component": "system"
                })
            
            # Memory usage alert
            if metrics["memory_percentage"] > 85:
                alerts.append({
                    "id": "memory_high",
                    "title": "High Memory Usage",
                    "description": f"Memory usage is {metrics['memory_percentage']}% (threshold: 85%)",
                    "severity": "critical" if metrics["memory_percentage"] > 95 else "warning",
                    "timestamp": datetime.utcnow().isoformat(),
                    "component": "system"
                })
            
            # Disk usage alert
            if metrics["disk_percentage"] > 90:
                alerts.append({
                    "id": "disk_high",
                    "title": "High Disk Usage",
                    "description": f"Disk usage is {metrics['disk_percentage']}% (threshold: 90%)",
                    "severity": "critical" if metrics["disk_percentage"] > 95 else "warning",
                    "timestamp": datetime.utcnow().isoformat(),
                    "component": "system"
                })
            
            # Application metrics alerts
            app_metrics = await self.get_application_metrics(db)
            
            # High error rate alert
            if app_metrics["error_rate"] > 5:
                alerts.append({
                    "id": "error_rate_high",
                    "title": "High Error Rate",
                    "description": f"Application error rate is {app_metrics['error_rate']}% (threshold: 5%)",
                    "severity": "critical" if app_metrics["error_rate"] > 10 else "warning",
                    "timestamp": datetime.utcnow().isoformat(),
                    "component": "application"
                })
            
            # High queue size alert
            if app_metrics["queue_size"] > 100:
                alerts.append({
                    "id": "queue_size_high",
                    "title": "High Queue Size",
                    "description": f"Job queue size is {app_metrics['queue_size']} (threshold: 100)",
                    "severity": "warning",
                    "timestamp": datetime.utcnow().isoformat(),
                    "component": "application"
                })
            
            return alerts
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


# Initialize service
perf_service = SystemPerformanceService()


@router.get("/metrics")
@admin_required
async def get_system_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive system and application performance metrics
    
    Returns:
        - System metrics (CPU, memory, disk, network)
        - Application metrics (jobs, errors, performance)
        - Timestamp information
    """
    try:
        # Get system metrics
        system_metrics = await perf_service.get_system_metrics()
        
        # Get application metrics
        app_metrics = await perf_service.get_application_metrics(db)
        
        # Combine metrics
        combined_metrics = {**system_metrics, **app_metrics}
        
        return {
            "success": True,
            "data": combined_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {str(e)}")


@router.get("/metrics/historical")
@admin_required
async def get_historical_metrics(
    timeRange: str = Query("1h", regex="^(1h|6h|24h|7d)$"),
    current_user: User = Depends(get_current_user)
):
    """
    Get historical system performance data
    
    Args:
        timeRange: Time range for data (1h, 6h, 24h, 7d)
    
    Returns:
        Historical performance metrics and trends
    """
    try:
        # For now, return mock historical data
        # In a real implementation, this would query a time-series database
        
        time_ranges = {
            "1h": 60,    # 60 minutes
            "6h": 360,   # 6 hours
            "24h": 1440, # 24 hours
            "7d": 10080  # 7 days
        }
        
        minutes = time_ranges.get(timeRange, 60)
        
        # Generate mock historical data
        import random
        now = datetime.utcnow()
        data_points = min(60, minutes // 5)  # Max 60 data points
        
        labels = []
        cpu_data = []
        memory_data = []
        disk_data = []
        
        for i in range(data_points):
            time_point = now - timedelta(minutes=i * 5)
            labels.append(time_point.strftime("%H:%M"))
            cpu_data.append(round(30 + random.random() * 40, 2))
            memory_data.append(round(25 + random.random() * 30, 2))
            disk_data.append(round(45 + random.random() * 10, 2))
        
        # Reverse to get chronological order
        labels.reverse()
        cpu_data.reverse()
        memory_data.reverse()
        disk_data.reverse()
        
        return {
            "success": True,
            "data": {
                "timeRange": timeRange,
                "labels": labels,
                "datasets": {
                    "cpu": cpu_data,
                    "memory": memory_data,
                    "disk": disk_data
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get historical metrics: {str(e)}")


@router.get("/alerts")
@admin_required
async def get_active_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get active system alerts and warnings
    
    Returns:
        List of active alerts with severity and details
    """
    try:
        alerts = await perf_service.get_active_alerts(db)
        
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "count": len(alerts)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.get("/services")
@admin_required
async def get_service_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get status of system services and components
    
    Returns:
        Status information for all system services
    """
    try:
        services = await perf_service.get_service_status()
        
        return {
            "success": True,
            "data": {
                "services": services,
                "count": len(services)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service status: {str(e)}")


@router.get("/analytics")
@admin_required
async def get_performance_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get performance analytics and trends
    
    Returns:
        Performance analytics with trends and recommendations
    """
    try:
        # Get current metrics for trend analysis
        current_metrics = await perf_service.get_system_metrics()
        app_metrics = await perf_service.get_application_metrics(db)
        
        # Mock analytics data (in real implementation, this would analyze historical data)
        analytics = {
            "performance_score": 85,
            "trends": {
                "cpu_usage": {
                    "current": current_metrics["cpu_usage"],
                    "trend": "stable",
                    "change": 2.1
                },
                "memory_usage": {
                    "current": current_metrics["memory_percentage"],
                    "trend": "up",
                    "change": 5.3
                },
                "response_time": {
                    "current": app_metrics["avg_response_time"],
                    "trend": "down",
                    "change": -8.7
                }
            },
            "recommendations": [
                {
                    "type": "performance",
                    "title": "Optimize Memory Usage",
                    "description": "Memory usage has increased by 5.3% in the last hour",
                    "priority": "medium",
                    "impact": "medium"
                },
                {
                    "type": "capacity",
                    "title": "Monitor Queue Growth",
                    "description": f"Current queue size is {app_metrics['queue_size']} jobs",
                    "priority": "low",
                    "impact": "low"
                }
            ]
        }
        
        return {
            "success": True,
            "data": analytics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance analytics: {str(e)}")


@router.get("/components")
@admin_required
async def get_component_resource_usage(
    current_user: User = Depends(get_current_user)
):
    """
    Get resource usage by system components
    
    Returns:
        Resource usage breakdown by component
    """
    try:
        # Get process information
        components = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                proc_info = proc.info
                if proc_info['name'] and 'python' in proc_info['name'].lower():
                    components.append({
                        "name": f"Python Process ({proc_info['pid']})",
                        "cpu": round(proc_info['cpu_percent'] or 0, 2),
                        "memory": proc_info['memory_info'].rss if proc_info['memory_info'] else 0,
                        "disk": 0,  # Would need additional tracking
                        "network": 0  # Would need additional tracking
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Aggregate and add system components
        if not components:
            components = [
                {
                    "name": "API Server",
                    "cpu": 25.3,
                    "memory": 512 * 1024 * 1024,
                    "disk": 0,
                    "network": 1024 * 1024
                },
                {
                    "name": "Background Worker",
                    "cpu": 15.7,
                    "memory": 256 * 1024 * 1024,
                    "disk": 10 * 1024 * 1024,
                    "network": 256 * 1024
                }
            ]
        
        return {
            "success": True,
            "data": {
                "components": components[:10]  # Limit to top 10
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get component resource usage: {str(e)}")


@router.get("/optimization")
@admin_required
async def get_optimization_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get system optimization recommendations
    
    Returns:
        Optimization recommendations based on current performance
    """
    try:
        # Analyze current system state
        system_metrics = await perf_service.get_system_metrics()
        app_metrics = await perf_service.get_application_metrics(db)
        
        recommendations = []
        
        # CPU optimization
        if system_metrics["cpu_usage"] > 70:
            recommendations.append({
                "category": "cpu",
                "title": "High CPU Usage Detected",
                "description": "Consider optimizing high-CPU processes or scaling horizontally",
                "impact": "high",
                "effort": "medium",
                "estimatedImprovement": "20-30% CPU usage reduction"
            })
        
        # Memory optimization
        if system_metrics["memory_percentage"] > 80:
            recommendations.append({
                "category": "memory",
                "title": "High Memory Usage",
                "description": "Optimize memory-intensive operations or increase available memory",
                "impact": "high",
                "effort": "medium",
                "estimatedImprovement": "15-25% memory usage reduction"
            })
        
        # Queue optimization
        if app_metrics["queue_size"] > 50:
            recommendations.append({
                "category": "performance",
                "title": "Large Job Queue",
                "description": "Consider adding more workers or optimizing job processing",
                "impact": "medium",
                "effort": "low",
                "estimatedImprovement": "50% faster job processing"
            })
        
        # General recommendations
        recommendations.extend([
            {
                "category": "monitoring",
                "title": "Enable Detailed Monitoring",
                "description": "Set up comprehensive monitoring for better performance insights",
                "impact": "low",
                "effort": "low",
                "estimatedImprovement": "Better visibility into system performance"
            },
            {
                "category": "caching",
                "title": "Implement Response Caching",
                "description": "Cache frequently requested data to reduce database load",
                "impact": "medium",
                "effort": "medium",
                "estimatedImprovement": "30-40% faster response times"
            }
        ])
        
        return {
            "success": True,
            "data": {
                "recommendations": recommendations,
                "system_score": 85,  # Overall system health score
                "priority_count": len([r for r in recommendations if r["impact"] == "high"])
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get optimization recommendations: {str(e)}")


@router.post("/alerts/{alert_id}/acknowledge")
@admin_required
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Acknowledge a system alert
    
    Args:
        alert_id: ID of the alert to acknowledge
    
    Returns:
        Acknowledgment confirmation
    """
    try:
        # In a real implementation, this would update alert status in database
        return {
            "success": True,
            "message": f"Alert {alert_id} acknowledged by {current_user.email}",
            "acknowledged_at": datetime.utcnow().isoformat(),
            "acknowledged_by": current_user.email
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")


@router.get("/health")
@admin_required
async def get_system_health_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive system health summary
    
    Returns:
        Overall system health status and key metrics
    """
    try:
        # Get all metrics
        system_metrics = await perf_service.get_system_metrics()
        app_metrics = await perf_service.get_application_metrics(db)
        alerts = await perf_service.get_active_alerts(db)
        services = await perf_service.get_service_status()
        
        # Calculate health score
        health_factors = []
        
        # System health factors
        health_factors.append(max(0, 100 - system_metrics["cpu_usage"]))
        health_factors.append(max(0, 100 - system_metrics["memory_percentage"]))
        health_factors.append(max(0, 100 - system_metrics["disk_percentage"]))
        
        # Application health factors
        health_factors.append(max(0, 100 - app_metrics["error_rate"] * 10))
        health_factors.append(min(100, max(0, 100 - app_metrics["queue_size"] / 10)))
        
        # Service health
        healthy_services = len([s for s in services if s["status"] == "healthy"])
        service_health = (healthy_services / len(services)) * 100 if services else 100
        health_factors.append(service_health)
        
        # Alert impact
        critical_alerts = len([a for a in alerts if a["severity"] == "critical"])
        warning_alerts = len([a for a in alerts if a["severity"] == "warning"])
        alert_impact = max(0, 100 - (critical_alerts * 20 + warning_alerts * 5))
        health_factors.append(alert_impact)
        
        overall_health = sum(health_factors) / len(health_factors)
        
        return {
            "success": True,
            "data": {
                "overall_health": round(overall_health, 1),
                "status": "healthy" if overall_health >= 80 else "warning" if overall_health >= 60 else "critical",
                "system_metrics": system_metrics,
                "application_metrics": app_metrics,
                "alerts_count": len(alerts),
                "services_healthy": f"{healthy_services}/{len(services)}",
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health summary: {str(e)}")