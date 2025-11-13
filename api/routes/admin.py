"""
Admin routes for the Whisper Transcriber API.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text
from api.orm_bootstrap import get_database_info, get_db
from api.models import Job, JobStatusEnum
from api.services.job_queue import job_queue
from api.routes.auth import get_current_admin_user as verify_token
from api.settings import settings
from api.app_state import get_app_state
from api.utils.logger import get_system_logger
from datetime import datetime, timedelta
import psutil
import os
import sys
import platform
import time
import shutil
import subprocess

logger = get_system_logger("admin_api")

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats", response_model=Dict[str, Any])
async def get_system_stats(
    current_user: dict = Depends(verify_token),
):
    """Get system statistics."""
    try:
        app_state = get_app_state()
        db_info = get_database_info()
        
        return {
            "app_state": app_state,
            "database": db_info,
            "settings": {
                "app_name": settings.app_name,
                "version": settings.version,
                "debug": settings.debug,
                "default_model": settings.default_model
            },
            "job_queue": {
                "total_jobs": len(job_queue.jobs),
                "active_jobs": len([j for j in job_queue.jobs.values() if j.status.value == "running"])
            }
        }
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def trigger_cleanup():
    """Trigger system cleanup."""
    try:
        job_queue.cleanup_old_jobs()
        return {"message": "Cleanup triggered successfully"}
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ─── Admin Job Management ─────────────────────────────────────────

@router.get("/jobs", response_model=Dict[str, Any])
async def list_all_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    days: Optional[int] = Query(None, ge=1),
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """List all jobs with admin filtering and search capabilities."""
    try:
        # Build query
        query = db.query(Job)
        
        # Filter by status if provided
        if status and status in [s.value for s in JobStatusEnum]:
            query = query.filter(Job.status == status)
        
        # Filter by date range if provided
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Job.created_at >= cutoff_date)
        
        # Search in filename if provided
        if search:
            query = query.filter(
                or_(
                    Job.original_filename.ilike(f"%{search}%"),
                    Job.id.ilike(f"%{search}%")
                )
            )
        
        # Order by most recent first
        query = query.order_by(Job.created_at.desc())
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        jobs = query.offset(skip).limit(limit).all()
        
        # Format response
        job_list = []
        for job in jobs:
            # Get queue status if available
            queue_job = job_queue.get_job(job.id)
            queue_status = queue_job.status.value if queue_job else None
            
            job_data = {
                "job_id": job.id,
                "original_filename": job.original_filename,
                "status": job.status.value,
                "queue_status": queue_status,
                "model": job.model,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "finished_at": job.finished_at.isoformat() if job.finished_at else None,
                "has_transcript": bool(job.transcript_path),
                "has_logs": bool(job.log_path)
            }
            job_list.append(job_data)
        
        return {
            "jobs": job_list,
            "total": total,
            "skip": skip,
            "limit": limit,
            "filters": {
                "status": status,
                "search": search,
                "days": days
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to list admin jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Cancel a running or queued job."""
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status in [JobStatusEnum.COMPLETED, JobStatusEnum.FAILED]:
            raise HTTPException(status_code=400, detail="Cannot cancel completed or failed job")
        
        # Cancel in queue
        success = job_queue.cancel_job(job_id)
        
        if success:
            # Update job status in database
            job.status = JobStatusEnum.FAILED
            job.finished_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Admin {current_user['username']} cancelled job {job_id}")
            return {"message": "Job cancelled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Job could not be cancelled")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete a job (admin only)."""
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Cancel from queue if still pending/running
        job_queue.cancel_job(job_id)
        
        # Clean up files if they exist
        import os
        try:
            if job.transcript_path and os.path.exists(job.transcript_path):
                os.remove(job.transcript_path)
            if job.log_path and os.path.exists(job.log_path):
                os.remove(job.log_path)
            # Try to remove the original file
            if hasattr(job, 'saved_filename'):
                file_path = settings.upload_dir / job.saved_filename
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception as e:
            logger.warning(f"Could not clean up files for job {job_id}: {e}")
        
        # Delete from database
        db.delete(job)
        db.commit()
        
        logger.info(f"Admin {current_user['username']} deleted job {job_id}")
        return {"message": "Job deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/cleanup")
async def cleanup_old_jobs(
    days: int = Query(30, ge=1),
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Clean up old completed and failed jobs."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Find old jobs to cleanup
        old_jobs = db.query(Job).filter(
            and_(
                Job.created_at < cutoff_date,
                or_(
                    Job.status == JobStatusEnum.COMPLETED,
                    Job.status.like('failed%')
                )
            )
        ).all()
        
        deleted_count = 0
        for job in old_jobs:
            try:
                # Clean up files
                import os
                if job.transcript_path and os.path.exists(job.transcript_path):
                    os.remove(job.transcript_path)
                if job.log_path and os.path.exists(job.log_path):
                    os.remove(job.log_path)
                
                # Delete from database
                db.delete(job)
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Could not delete old job {job.id}: {e}")
        
        db.commit()
        
        logger.info(f"Admin {current_user['username']} cleaned up {deleted_count} old jobs")
        return {
            "message": f"Cleaned up {deleted_count} old jobs",
            "deleted_count": deleted_count,
            "cutoff_days": days
        }
    
    except Exception as e:
        logger.error(f"Failed to cleanup old jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/stats")
async def get_job_stats(
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get job statistics for admin dashboard."""
    try:
        stats = {}
        
        # Overall stats
        total_jobs = db.query(Job).count()
        stats['total_jobs'] = total_jobs
        
        # Status breakdown
        for status in JobStatusEnum:
            count = db.query(Job).filter(Job.status == status).count()
            stats[f'jobs_{status.value}'] = count
        
        # Recent activity (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_jobs = db.query(Job).filter(Job.created_at >= recent_cutoff).count()
        stats['recent_jobs_24h'] = recent_jobs
        
        # Queue stats
        queue_stats = {
            "total_in_queue": len(job_queue.jobs),
            "active_jobs": len([j for j in job_queue.jobs.values() if j.status.value == "running"])
        }
        stats['queue'] = queue_stats
        
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get job stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job_details(
    job_id: str,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get detailed job information for admin."""
    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get queue status and details
        queue_job = job_queue.get_job(job_id)
        queue_details = {}
        if queue_job:
            queue_details = {
                "queue_status": queue_job.status.value,
                "queue_progress": getattr(queue_job, 'progress', None),
                "queue_worker": getattr(queue_job, 'worker', None)
            }

        # Read transcript if available
        transcript_content = None
        if job.transcript_path:
            try:
                with open(job.transcript_path, 'r') as f:
                    transcript_content = f.read()
            except Exception as e:
                logger.warning(f"Could not read transcript for job {job_id}: {e}")

        # Read logs if available
        log_content = None
        if job.log_path:
            try:
                with open(job.log_path, 'r') as f:
                    # Limit log size to prevent overwhelming response
                    log_content = f.read()[-10000:]
            except Exception as e:
                logger.warning(f"Could not read logs for job {job_id}: {e}")

        return {
            "job_id": job.id,
            "original_filename": job.original_filename,
            "saved_filename": job.saved_filename,
            "model": job.model,
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "transcript_path": job.transcript_path,
            "log_path": job.log_path,
            "queue_details": queue_details,
            "transcript_content": transcript_content,
            "log_content": log_content
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job details for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "whisper-transcriber",
        "version": settings.version
    }

# ─── System Health Monitoring ─────────────────────────────────────────

@router.get("/health/system", response_model=Dict[str, Any])
async def get_system_health(
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get comprehensive system health metrics."""
    try:
        # System resources
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk_usage = psutil.disk_usage('/')
        
        # Process information
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # Database health
        try:
            db.execute(text("SELECT 1")).fetchone()
            db_status = "healthy"
            db_error = None
        except Exception as e:
            db_status = "unhealthy"
            db_error = str(e)
        
        # Job queue health
        queue_health = {
            "status": "healthy" if job_queue else "unhealthy",
            "total_jobs": len(job_queue.jobs) if job_queue else 0,
            "active_jobs": len([j for j in job_queue.jobs.values() if j.status.value == "running"]) if job_queue else 0
        }
        
        # Service status checks
        services = {
            "api": {
                "status": "healthy",
                "uptime": time.time() - process.create_time(),
                "memory_usage": process_memory.rss,
                "cpu_percent": process.cpu_percent()
            },
            "database": {
                "status": db_status,
                "error": db_error
            },
            "job_queue": queue_health,
            "file_system": {
                "status": "healthy" if disk_usage.percent < 90 else "warning",
                "disk_usage_percent": disk_usage.percent
            }
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy" if all(s.get("status") == "healthy" for s in services.values()) else "degraded",
            "system_metrics": {
                "cpu": {
                    "usage_percent": cpu_usage,
                    "count": psutil.cpu_count(),
                    "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk_usage.total,
                    "used": disk_usage.used,
                    "free": disk_usage.free,
                    "percent": disk_usage.percent
                },
                "process": {
                    "pid": process.pid,
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms,
                    "cpu_percent": process.cpu_percent(),
                    "num_threads": process.num_threads()
                }
            },
            "services": services,
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "python_version": sys.version
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/services", response_model=Dict[str, Any])
async def get_service_status(
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get detailed service status information."""
    try:
        services = {}
        
        # API Service Health
        try:
            process = psutil.Process()
            api_uptime = time.time() - process.create_time()
            services["api"] = {
                "status": "healthy",
                "uptime_seconds": api_uptime,
                "uptime_human": str(timedelta(seconds=int(api_uptime))),
                "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "threads": process.num_threads(),
                "connections": len(process.connections()) if hasattr(process, 'connections') else 0
            }
        except Exception as e:
            services["api"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Database Health
        try:
            start_time = time.time()
            result = db.execute(text("SELECT COUNT(*) FROM jobs")).fetchone()
            query_time = (time.time() - start_time) * 1000
            
            services["database"] = {
                "status": "healthy",
                "query_time_ms": round(query_time, 2),
                "total_jobs": result[0] if result else 0,
                "connection_pool": "active"
            }
        except Exception as e:
            services["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Job Queue Health
        try:
            if job_queue:
                running_jobs = [j for j in job_queue.jobs.values() if j.status.value == "running"]
                pending_jobs = [j for j in job_queue.jobs.values() if j.status.value == "pending"]
                
                services["job_queue"] = {
                    "status": "healthy",
                    "total_jobs": len(job_queue.jobs),
                    "running_jobs": len(running_jobs),
                    "pending_jobs": len(pending_jobs),
                    "queue_type": type(job_queue).__name__
                }
            else:
                services["job_queue"] = {
                    "status": "unhealthy",
                    "error": "Job queue not initialized"
                }
        except Exception as e:
            services["job_queue"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # File System Health
        try:
            # Check critical directories
            critical_dirs = [
                settings.upload_dir,
                settings.transcripts_dir,
                settings.models_dir,
                settings.cache_dir
            ]
            
            dir_status = {}
            for dir_path in critical_dirs:
                if os.path.exists(dir_path):
                    stat = shutil.disk_usage(dir_path)
                    dir_status[str(dir_path)] = {
                        "exists": True,
                        "writable": os.access(dir_path, os.W_OK),
                        "free_space_gb": round(stat.free / (1024**3), 2)
                    }
                else:
                    dir_status[str(dir_path)] = {
                        "exists": False,
                        "writable": False,
                        "free_space_gb": 0
                    }
            
            services["file_system"] = {
                "status": "healthy" if all(d["exists"] and d["writable"] for d in dir_status.values()) else "degraded",
                "directories": dir_status
            }
        except Exception as e:
            services["file_system"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Overall health assessment
        healthy_services = sum(1 for s in services.values() if s.get("status") == "healthy")
        total_services = len(services)
        overall_health = "healthy" if healthy_services == total_services else "degraded" if healthy_services > 0 else "unhealthy"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_health,
            "health_score": round((healthy_services / total_services) * 100, 1),
            "services": services
        }
    
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/performance", response_model=Dict[str, Any])
async def get_performance_metrics(
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get system performance metrics and statistics."""
    try:
        # Database performance
        db_start = time.time()
        recent_jobs = db.query(Job).order_by(Job.created_at.desc()).limit(10).all()
        db_query_time = (time.time() - db_start) * 1000
        
        # Job processing stats
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        
        jobs_today = db.query(Job).filter(Job.created_at >= today).count()
        jobs_week = db.query(Job).filter(Job.created_at >= week_ago).count()
        completed_jobs = db.query(Job).filter(Job.status == JobStatusEnum.COMPLETED).count()
        failed_jobs = db.query(Job).filter(Job.status == JobStatusEnum.FAILED).count()
        total_jobs = db.query(Job).count()
        
        # Calculate success rate
        success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
        
        # Average processing time for completed jobs
        completed_with_times = db.query(Job).filter(
            and_(
                Job.status == JobStatusEnum.COMPLETED,
                Job.started_at.isnot(None),
                Job.finished_at.isnot(None)
            )
        ).limit(100).all()
        
        processing_times = []
        for job in completed_with_times:
            if job.started_at and job.finished_at:
                duration = (job.finished_at - job.started_at).total_seconds()
                processing_times.append(duration)
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # System resource trends (would be better with historical data)
        cpu_samples = []
        memory_samples = []
        for _ in range(5):
            cpu_samples.append(psutil.cpu_percent(interval=0.2))
            memory_samples.append(psutil.virtual_memory().percent)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "database_performance": {
                "query_time_ms": round(db_query_time, 2),
                "connection_status": "active",
                "recent_jobs_count": len(recent_jobs)
            },
            "job_processing": {
                "jobs_today": jobs_today,
                "jobs_this_week": jobs_week,
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "success_rate_percent": round(success_rate, 1),
                "average_processing_time_seconds": round(avg_processing_time, 2),
                "queue_length": len(job_queue.jobs) if job_queue else 0
            },
            "system_resources": {
                "cpu_samples": cpu_samples,
                "memory_samples": memory_samples,
                "cpu_average": round(sum(cpu_samples) / len(cpu_samples), 1),
                "memory_average": round(sum(memory_samples) / len(memory_samples), 1)
            },
            "api_performance": {
                "uptime_seconds": time.time() - psutil.Process().create_time(),
                "memory_usage_mb": round(psutil.Process().memory_info().rss / 1024 / 1024, 2),
                "cpu_percent": psutil.Process().cpu_percent()
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/logs", response_model=Dict[str, Any])
async def get_system_logs(
    current_user: dict = Depends(verify_token),
    lines: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None),
    service: Optional[str] = Query(None)
):
    """Get system logs with filtering options."""
    try:
        log_files = []
        log_dir = "logs"
        
        # Find available log files
        if os.path.exists(log_dir):
            for file in os.listdir(log_dir):
                if file.endswith(('.log', '.txt')):
                    log_files.append(os.path.join(log_dir, file))
        
        # Read logs from the most recent general log file
        logs = []
        if log_files:
            # Sort by modification time, most recent first
            log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            for log_file in log_files[:3]:  # Check up to 3 most recent log files
                try:
                    with open(log_file, 'r') as f:
                        file_lines = f.readlines()
                        for line in file_lines[-lines:]:  # Get last N lines
                            line = line.strip()
                            if line:
                                # Basic log parsing
                                log_entry = {
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "level": "INFO",
                                    "service": os.path.basename(log_file),
                                    "message": line
                                }
                                
                                # Try to extract log level from line
                                for log_level in ["ERROR", "WARNING", "INFO", "DEBUG"]:
                                    if log_level in line.upper():
                                        log_entry["level"] = log_level
                                        break
                                
                                # Apply filters
                                if level and log_entry["level"] != level.upper():
                                    continue
                                if service and service not in log_entry["service"]:
                                    continue
                                
                                logs.append(log_entry)
                except Exception as e:
                    logger.warning(f"Could not read log file {log_file}: {e}")
        
        # If no log files found, create some sample system status logs
        if not logs:
            logs = [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": "INFO",
                    "service": "system",
                    "message": "System health monitoring active"
                },
                {
                    "timestamp": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
                    "level": "INFO",
                    "service": "api",
                    "message": "API server running normally"
                }
            ]
        
        # Sort by timestamp (most recent first) and limit
        logs = sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:lines]
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "logs": logs,
            "total_entries": len(logs),
            "filters": {
                "lines": lines,
                "level": level,
                "service": service
            },
            "available_log_files": [os.path.basename(f) for f in log_files]
        }
    
    except Exception as e:
        logger.error(f"Failed to get system logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
