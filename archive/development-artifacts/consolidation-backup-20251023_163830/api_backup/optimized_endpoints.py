"""
Optimized API endpoints using performance-enhanced query patterns
This module demonstrates the use of optimized queries to replace existing inefficient patterns
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Query as QueryParam
from sqlalchemy.orm import Session

from api.models import Job, User, TranscriptMetadata, JobStatusEnum
from api.query_optimizer import (
    OptimizedJobQueries,
    OptimizedUserQueries, 
    OptimizedMetadataQueries,
    OptimizedAuditLogQueries,
    performance_tracked
)


# ────────────────────────────────────────────────────────────────────────────
# Optimized Job Endpoints
# ────────────────────────────────────────────────────────────────────────────

@performance_tracked("LIST_JOBS", "jobs")
def list_jobs_optimized(
    db: Session,
    current_user: User,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    user_id: Optional[int] = None  # Admin can filter by user
) -> Dict[str, Any]:
    """
    Optimized job listing with pagination and efficient querying
    Replaces the N+1 query pattern in the original implementation
    """
    
    # Validate page parameters
    page = max(1, page)
    page_size = min(max(1, page_size), 100)  # Limit page size
    
    # Determine which user's jobs to show
    target_user_id = user_id if current_user.role == "admin" and user_id else current_user.id
    
    # Use optimized query with pagination
    jobs, total_count = OptimizedJobQueries.get_jobs_by_user_paginated(
        db=db,
        user_id=target_user_id,
        page=page,
        page_size=page_size,
        status=status
    )
    
    # Calculate pagination metadata
    total_pages = (total_count + page_size - 1) // page_size
    has_next = page < total_pages
    has_prev = page > 1
    
    return {
        "jobs": [
            {
                "id": job.id,
                "original_filename": job.original_filename,
                "status": job.status,
                "model": job.model,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "finished_at": job.finished_at.isoformat() if job.finished_at else None,
                "processing_time_seconds": job.processing_time_seconds,
                "file_size_bytes": job.file_size_bytes,
                "duration_seconds": job.duration_seconds
            }
            for job in jobs
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev
        }
    }


@performance_tracked("GET_JOB_DETAIL", "jobs")
def get_job_detail_optimized(
    db: Session,
    job_id: str,
    current_user: User,
    include_metadata: bool = True
) -> Dict[str, Any]:
    """
    Optimized job detail retrieval with metadata in single query
    Prevents N+1 queries by eager loading related data
    """
    
    # Use optimized query to get job with related data
    job = OptimizedJobQueries.get_job_with_user_and_metadata(db, job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check access permissions
    if current_user.role != "admin" and job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    job_data = {
        "id": job.id,
        "original_filename": job.original_filename,
        "saved_filename": job.saved_filename,
        "status": job.status,
        "model": job.model,
        "user_id": job.user_id,
        "transcript_path": job.transcript_path,
        "log_path": job.log_path,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "processing_time_seconds": job.processing_time_seconds,
        "file_size_bytes": job.file_size_bytes,
        "duration_seconds": job.duration_seconds
    }
    
    # Include metadata if requested and available
    if include_metadata and hasattr(job, 'metadata') and job.metadata:
        job_data["metadata"] = {
            "tokens": job.metadata.tokens,
            "duration": job.metadata.duration,
            "abstract": job.metadata.abstract,
            "sample_rate": job.metadata.sample_rate,
            "wpm": job.metadata.wpm,
            "keywords": job.metadata.keywords,
            "summary": job.metadata.summary,
            "language": job.metadata.language,
            "sentiment": job.metadata.sentiment,
            "generated_at": job.metadata.generated_at.isoformat()
        }
    
    return job_data


@performance_tracked("GET_JOB_STATISTICS", "jobs")
def get_job_statistics_optimized(
    db: Session,
    current_user: User,
    days: int = 30,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Optimized job statistics using aggregation queries
    Much more efficient than counting individual queries
    """
    
    # Validate parameters
    days = min(max(1, days), 365)  # Limit range
    
    # Determine target user
    target_user_id = user_id if current_user.role == "admin" and user_id else current_user.id
    
    # Get statistics using optimized aggregation query
    stats = OptimizedJobQueries.get_job_statistics(db, target_user_id, days)
    
    # Add additional context
    stats.update({
        "period_days": days,
        "user_id": target_user_id,
        "generated_at": datetime.utcnow().isoformat()
    })
    
    return stats


# ────────────────────────────────────────────────────────────────────────────
# Optimized Admin Dashboard Endpoints
# ────────────────────────────────────────────────────────────────────────────

@performance_tracked("ADMIN_DASHBOARD", "multiple")
def get_admin_dashboard_optimized(
    db: Session,
    current_user: User,
    hours: int = 24
) -> Dict[str, Any]:
    """
    Optimized admin dashboard with efficient aggregation queries
    Replaces multiple individual queries with optimized patterns
    """
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate parameters
    hours = min(max(1, hours), 168)  # Max 1 week
    
    # Get system statistics efficiently
    job_stats = OptimizedJobQueries.get_job_statistics(db, user_id=None, days=hours//24 or 1)
    metadata_stats = OptimizedMetadataQueries.get_metadata_analytics(db, days=hours//24 or 1)
    
    # Get active users with their statistics
    active_users = OptimizedUserQueries.get_active_users_with_stats(db, limit=10)
    
    # Get recent active jobs
    active_jobs = OptimizedJobQueries.get_recent_active_jobs(db, limit=10)
    
    # Get security events
    security_events = OptimizedAuditLogQueries.get_security_events(db, hours=hours, limit=20)
    
    return {
        "system_statistics": {
            "jobs": job_stats,
            "transcripts": metadata_stats,
            "period_hours": hours
        },
        "active_users": [
            {
                "id": user_data["user"].id,
                "username": user_data["user"].username,
                "role": user_data["user"].role,
                "total_jobs": user_data["total_jobs"],
                "completed_jobs": user_data["completed_jobs"],
                "success_rate": user_data["success_rate"],
                "last_job_date": user_data["last_job_date"].isoformat() if user_data["last_job_date"] else None,
                "last_login": user_data["user"].last_login.isoformat() if user_data["user"].last_login else None
            }
            for user_data in active_users
        ],
        "active_jobs": [
            {
                "id": job.id,
                "original_filename": job.original_filename,
                "status": job.status,
                "model": job.model,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
                "user_id": job.user_id
            }
            for job in active_jobs
        ],
        "recent_security_events": [
            {
                "id": event.id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "severity": event.severity,
                "username": event.username,
                "client_ip": event.client_ip,
                "endpoint": event.endpoint,
                "status_code": event.status_code
            }
            for event in security_events
        ],
        "generated_at": datetime.utcnow().isoformat()
    }


# ────────────────────────────────────────────────────────────────────────────
# Optimized User Activity Endpoints
# ────────────────────────────────────────────────────────────────────────────

@performance_tracked("USER_ACTIVITY", "audit_logs")
def get_user_activity_optimized(
    db: Session,
    current_user: User,
    user_id: Optional[int] = None,
    days: int = 7
) -> Dict[str, Any]:
    """
    Optimized user activity summary with efficient queries
    """
    
    # Determine target user
    if user_id and current_user.role == "admin":
        target_user_id = user_id
    elif user_id and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    else:
        target_user_id = current_user.id
    
    # Validate parameters
    days = min(max(1, days), 90)  # Max 90 days
    
    # Get user activity summary
    activity_summary = OptimizedAuditLogQueries.get_user_activity_summary(db, target_user_id, days)
    
    return {
        "user_id": target_user_id,
        "period_days": days,
        "activity_summary": activity_summary,
        "generated_at": datetime.utcnow().isoformat()
    }


# ────────────────────────────────────────────────────────────────────────────
# Optimized Search and Analytics Endpoints
# ────────────────────────────────────────────────────────────────────────────

@performance_tracked("SEARCH_JOBS", "jobs")
def search_jobs_optimized(
    db: Session,
    current_user: User,
    query: str,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Optimized job search with efficient filtering and pagination
    """
    
    # Validate parameters
    page = max(1, page)
    page_size = min(max(1, page_size), 50)  # Limit for search
    
    # Build optimized search query
    from sqlalchemy import and_, or_, func
    
    search_query = db.query(Job).filter(Job.user_id == current_user.id)
    
    # Add text search
    if query.strip():
        search_term = f"%{query.strip()}%"
        search_query = search_query.filter(
            or_(
                Job.original_filename.ilike(search_term),
                Job.id.ilike(search_term)
            )
        )
    
    # Add filters
    if status:
        search_query = search_query.filter(Job.status == status)
    
    if date_from:
        search_query = search_query.filter(Job.created_at >= date_from)
    
    if date_to:
        search_query = search_query.filter(Job.created_at <= date_to)
    
    # Get total count
    total_count = search_query.count()
    
    # Get paginated results
    offset = (page - 1) * page_size
    jobs = search_query.order_by(Job.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Calculate pagination
    total_pages = (total_count + page_size - 1) // page_size
    
    return {
        "query": query,
        "filters": {
            "status": status,
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None
        },
        "results": [
            {
                "id": job.id,
                "original_filename": job.original_filename,
                "status": job.status,
                "model": job.model,
                "created_at": job.created_at.isoformat(),
                "processing_time_seconds": job.processing_time_seconds
            }
            for job in jobs
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }
