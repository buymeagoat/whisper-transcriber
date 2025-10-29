"""Audit and logging routes for administrative oversight."""

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from ..routes.auth import get_current_admin_user as verify_token

# Create router instance
router = APIRouter(tags=["audit"])

# Response models
class AuditEvent(BaseModel):
    id: str
    timestamp: datetime
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: dict
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditSummary(BaseModel):
    total_events: int
    events_last_24h: int
    events_last_7d: int
    top_actions: List[dict]
    top_users: List[dict]

# Mock audit data store
AUDIT_EVENTS = []

def add_audit_event(action: str, resource_type: str, resource_id: Optional[str] = None, 
                   details: Optional[dict] = None, user_id: Optional[str] = None):
    """Add an audit event to the log."""
    event = AuditEvent(
        id=f"audit_{len(AUDIT_EVENTS) + 1}",
        timestamp=datetime.utcnow(),
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address="127.0.0.1",  # Would be extracted from request in production
        user_agent="Test Agent"
    )
    AUDIT_EVENTS.append(event)
    return event

@router.get("/events", response_model=List[AuditEvent])
async def get_audit_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    action_filter: Optional[str] = Query(None),
    resource_type_filter: Optional[str] = Query(None),
    user_id_filter: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(verify_token)
):
    """Retrieve audit events with filtering and pagination."""
    
    # Filter events
    filtered_events = AUDIT_EVENTS.copy()
    
    if action_filter:
        filtered_events = [e for e in filtered_events if action_filter.lower() in e.action.lower()]
    
    if resource_type_filter:
        filtered_events = [e for e in filtered_events if resource_type_filter.lower() in e.resource_type.lower()]
    
    if user_id_filter:
        filtered_events = [e for e in filtered_events if e.user_id == user_id_filter]
    
    if start_date:
        filtered_events = [e for e in filtered_events if e.timestamp >= start_date]
    
    if end_date:
        filtered_events = [e for e in filtered_events if e.timestamp <= end_date]
    
    # Sort by timestamp (newest first)
    filtered_events.sort(key=lambda x: x.timestamp, reverse=True)
    
    # Apply pagination
    paginated_events = filtered_events[offset:offset + limit]
    
    return paginated_events

@router.get("/events/{event_id}", response_model=AuditEvent)
async def get_audit_event(
    event_id: str,
    current_user: dict = Depends(verify_token)
):
    """Retrieve a specific audit event by ID."""
    event = next((e for e in AUDIT_EVENTS if e.id == event_id), None)
    if not event:
        raise HTTPException(status_code=404, detail="Audit event not found")
    return event

@router.get("/summary", response_model=AuditSummary)
async def get_audit_summary(
    current_user: dict = Depends(verify_token)
):
    """Get audit summary statistics."""
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    
    events_last_24h = len([e for e in AUDIT_EVENTS if e.timestamp >= last_24h])
    events_last_7d = len([e for e in AUDIT_EVENTS if e.timestamp >= last_7d])
    
    # Count actions
    action_counts = {}
    user_counts = {}
    
    for event in AUDIT_EVENTS:
        action_counts[event.action] = action_counts.get(event.action, 0) + 1
        if event.user_id:
            user_counts[event.user_id] = user_counts.get(event.user_id, 0) + 1
    
    # Get top actions and users
    top_actions = [
        {"action": action, "count": count}
        for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
    
    top_users = [
        {"user_id": user_id, "count": count}
        for user_id, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
    
    return AuditSummary(
        total_events=len(AUDIT_EVENTS),
        events_last_24h=events_last_24h,
        events_last_7d=events_last_7d,
        top_actions=top_actions,
        top_users=top_users
    )

@router.delete("/events")
async def clear_audit_events(
    confirm: bool = Query(False),
    current_user: dict = Depends(verify_token)
):
    """Clear all audit events (requires confirmation)."""
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Must set confirm=true to clear audit events"
        )
    
    # Add audit event for clearing audit log
    add_audit_event(
        action="audit_clear",
        resource_type="audit_log",
        details={"cleared_count": len(AUDIT_EVENTS)},
        user_id=current_user["username"]
    )
    
    # Clear events (except the clear event we just added)
    last_event = AUDIT_EVENTS[-1]
    AUDIT_EVENTS.clear()
    AUDIT_EVENTS.append(last_event)
    
    return {"message": "Audit events cleared successfully"}

# Initialize with some sample audit events
if not AUDIT_EVENTS:
    sample_events = [
        ("user_login", "authentication", "user_1", {"method": "password"}),
        ("job_created", "transcription_job", "job_123", {"filename": "audio.wav"}),
        ("job_completed", "transcription_job", "job_123", {"duration": 45.2}),
        ("user_logout", "authentication", "user_1", {"session_duration": 300}),
        ("admin_access", "admin_panel", None, {"section": "settings"}),
    ]
    
    for action, resource_type, resource_id, details in sample_events:
        add_audit_event(action, resource_type, resource_id, details, "admin")