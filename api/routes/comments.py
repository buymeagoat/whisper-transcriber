"""
T036: Real-time Collaboration Features - Comments & Annotations API Routes
API endpoints for managing comments, annotations, and notifications.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from ..database import get_db
from ..auth import get_current_user
from ..services.comments_annotations import (
    CommentManager, AnnotationManager, CommentType, 
    AnnotationType, CommentPosition, NotificationStatus
)
from ..services.workspace_manager import WorkspaceManager, ProjectManager
from ..schemas import User
from ..utils.logger import get_logger

logger = get_logger("comments_routes")

router = APIRouter(prefix="/api/v1", tags=["comments", "annotations"])
security = HTTPBearer()


# Comment Management Endpoints

@router.post("/documents/{document_id}/comments", status_code=status.HTTP_201_CREATED)
async def create_comment(
    document_id: str,
    content: str,
    comment_type: str = "general",
    parent_id: Optional[str] = None,
    start_position: Optional[int] = None,
    end_position: Optional[int] = None,
    line_number: Optional[int] = None,
    selected_text: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new comment on a document."""
    try:
        comment_manager = CommentManager(db)
        project_manager = ProjectManager(db)
        workspace_manager = WorkspaceManager(db)
        
        # Verify document exists and user has access
        document = project_manager.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check workspace access
        project = project_manager.get_project(document.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        role = workspace_manager.get_member_role(project.workspace_id, current_user.id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to document"
            )
        
        # Validate comment type
        try:
            comment_type_enum = CommentType(comment_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid comment type: {comment_type}"
            )
        
        # Create position if provided
        position = None
        if start_position is not None and end_position is not None:
            position = CommentPosition(
                start_position=start_position,
                end_position=end_position,
                line_number=line_number,
                selected_text=selected_text
            )
        
        # Create comment
        comment = comment_manager.create_comment(
            document_id=document_id,
            author_id=current_user.id,
            content=content,
            comment_type=comment_type_enum,
            position=position,
            parent_id=parent_id
        )
        
        return {
            "id": comment.id,
            "content": comment.content,
            "comment_type": comment.comment_type,
            "status": comment.status,
            "author_id": comment.author_id,
            "author_name": comment.author.username,
            "parent_id": comment.parent_id,
            "start_position": comment.start_position,
            "end_position": comment.end_position,
            "line_number": comment.line_number,
            "selected_text": comment.selected_text,
            "created_at": comment.created_at.isoformat(),
            "updated_at": comment.updated_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create comment: {str(e)}"
        )


@router.get("/documents/{document_id}/comments")
async def get_document_comments(
    document_id: str,
    include_resolved: bool = Query(False, description="Include resolved comments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all comments for a document."""
    try:
        comment_manager = CommentManager(db)
        project_manager = ProjectManager(db)
        workspace_manager = WorkspaceManager(db)
        
        # Verify document access
        document = project_manager.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        project = project_manager.get_project(document.project_id)
        role = workspace_manager.get_member_role(project.workspace_id, current_user.id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to document"
            )
        
        # Get comments
        comments = comment_manager.get_document_comments(document_id, include_resolved)
        
        # Group comments by thread
        comment_threads = {}
        for comment in comments:
            if comment.parent_id:
                # This is a reply
                if comment.parent_id not in comment_threads:
                    comment_threads[comment.parent_id] = {"replies": []}
                comment_threads[comment.parent_id]["replies"].append({
                    "id": comment.id,
                    "content": comment.content,
                    "comment_type": comment.comment_type,
                    "status": comment.status,
                    "author_id": comment.author_id,
                    "author_name": comment.author.username,
                    "parent_id": comment.parent_id,
                    "created_at": comment.created_at.isoformat(),
                    "updated_at": comment.updated_at.isoformat()
                })
            else:
                # This is a parent comment
                if comment.id not in comment_threads:
                    comment_threads[comment.id] = {"replies": []}
                
                comment_threads[comment.id]["comment"] = {
                    "id": comment.id,
                    "content": comment.content,
                    "comment_type": comment.comment_type,
                    "status": comment.status,
                    "author_id": comment.author_id,
                    "author_name": comment.author.username,
                    "start_position": comment.start_position,
                    "end_position": comment.end_position,
                    "line_number": comment.line_number,
                    "selected_text": comment.selected_text,
                    "created_at": comment.created_at.isoformat(),
                    "updated_at": comment.updated_at.isoformat()
                }
        
        # Format response
        result = []
        for thread_id, thread_data in comment_threads.items():
            if "comment" in thread_data:
                thread_data["comment"]["replies"] = thread_data["replies"]
                result.append(thread_data["comment"])
        
        return {"comments": result}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document comments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comments: {str(e)}"
        )


@router.get("/comments/{comment_id}/thread")
async def get_comment_thread(
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a complete comment thread."""
    try:
        comment_manager = CommentManager(db)
        project_manager = ProjectManager(db)
        workspace_manager = WorkspaceManager(db)
        
        # Get the comment first to check access
        comment = comment_manager.get_comment(comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Verify document access
        document = project_manager.get_document(comment.document_id)
        project = project_manager.get_project(document.project_id)
        role = workspace_manager.get_member_role(project.workspace_id, current_user.id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to comment"
            )
        
        # Get thread
        thread = comment_manager.get_comment_thread(comment_id)
        
        result = []
        for comment in thread:
            result.append({
                "id": comment.id,
                "content": comment.content,
                "comment_type": comment.comment_type,
                "status": comment.status,
                "author_id": comment.author_id,
                "author_name": comment.author.username,
                "parent_id": comment.parent_id,
                "start_position": comment.start_position,
                "end_position": comment.end_position,
                "line_number": comment.line_number,
                "selected_text": comment.selected_text,
                "created_at": comment.created_at.isoformat(),
                "updated_at": comment.updated_at.isoformat()
            })
        
        return {"thread": result}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting comment thread: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comment thread: {str(e)}"
        )


@router.put("/comments/{comment_id}")
async def update_comment(
    comment_id: str,
    content: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a comment."""
    try:
        comment_manager = CommentManager(db)
        
        success = comment_manager.update_comment(comment_id, content, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found or access denied"
            )
        
        return {"message": "Comment updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update comment: {str(e)}"
        )


@router.post("/comments/{comment_id}/resolve")
async def resolve_comment(
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a comment as resolved."""
    try:
        comment_manager = CommentManager(db)
        
        success = comment_manager.resolve_comment(comment_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        return {"message": "Comment resolved successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve comment: {str(e)}"
        )


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a comment."""
    try:
        comment_manager = CommentManager(db)
        
        success = comment_manager.delete_comment(comment_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found or access denied"
            )
        
        return {"message": "Comment deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete comment: {str(e)}"
        )


@router.post("/comments/{comment_id}/reactions")
async def add_reaction(
    comment_id: str,
    reaction_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a reaction to a comment."""
    try:
        comment_manager = CommentManager(db)
        
        success = comment_manager.add_reaction(comment_id, current_user.id, reaction_type)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not add reaction (already exists or comment not found)"
            )
        
        return {"message": "Reaction added successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding reaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add reaction: {str(e)}"
        )


@router.delete("/comments/{comment_id}/reactions/{reaction_type}")
async def remove_reaction(
    comment_id: str,
    reaction_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a reaction from a comment."""
    try:
        comment_manager = CommentManager(db)
        
        success = comment_manager.remove_reaction(comment_id, current_user.id, reaction_type)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reaction not found"
            )
        
        return {"message": "Reaction removed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing reaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove reaction: {str(e)}"
        )


# Annotation Management Endpoints

@router.post("/documents/{document_id}/annotations", status_code=status.HTTP_201_CREATED)
async def create_annotation(
    document_id: str,
    annotation_type: str,
    start_position: int,
    end_position: int,
    selected_text: str = "",
    title: str = "",
    content: str = "",
    color: str = "#FFD700",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new annotation on a document."""
    try:
        annotation_manager = AnnotationManager(db)
        project_manager = ProjectManager(db)
        workspace_manager = WorkspaceManager(db)
        
        # Verify document access
        document = project_manager.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        project = project_manager.get_project(document.project_id)
        role = workspace_manager.get_member_role(project.workspace_id, current_user.id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to document"
            )
        
        # Validate annotation type
        try:
            annotation_type_enum = AnnotationType(annotation_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid annotation type: {annotation_type}"
            )
        
        # Create annotation
        annotation = annotation_manager.create_annotation(
            document_id=document_id,
            author_id=current_user.id,
            annotation_type=annotation_type_enum,
            start_position=start_position,
            end_position=end_position,
            selected_text=selected_text,
            title=title,
            content=content,
            color=color
        )
        
        return {
            "id": annotation.id,
            "annotation_type": annotation.annotation_type,
            "start_position": annotation.start_position,
            "end_position": annotation.end_position,
            "selected_text": annotation.selected_text,
            "title": annotation.title,
            "content": annotation.content,
            "color": annotation.color,
            "author_id": annotation.author_id,
            "author_name": annotation.author.username,
            "created_at": annotation.created_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating annotation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create annotation: {str(e)}"
        )


@router.get("/documents/{document_id}/annotations")
async def get_document_annotations(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all annotations for a document."""
    try:
        annotation_manager = AnnotationManager(db)
        project_manager = ProjectManager(db)
        workspace_manager = WorkspaceManager(db)
        
        # Verify document access
        document = project_manager.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        project = project_manager.get_project(document.project_id)
        role = workspace_manager.get_member_role(project.workspace_id, current_user.id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to document"
            )
        
        # Get annotations
        annotations = annotation_manager.get_document_annotations(document_id)
        
        result = []
        for annotation in annotations:
            result.append({
                "id": annotation.id,
                "annotation_type": annotation.annotation_type,
                "start_position": annotation.start_position,
                "end_position": annotation.end_position,
                "selected_text": annotation.selected_text,
                "title": annotation.title,
                "content": annotation.content,
                "color": annotation.color,
                "author_id": annotation.author_id,
                "author_name": annotation.author.username,
                "is_visible": annotation.is_visible,
                "created_at": annotation.created_at.isoformat(),
                "updated_at": annotation.updated_at.isoformat()
            })
        
        return {"annotations": result}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document annotations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get annotations: {str(e)}"
        )


@router.put("/annotations/{annotation_id}")
async def update_annotation(
    annotation_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    color: Optional[str] = None,
    is_visible: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an annotation."""
    try:
        annotation_manager = AnnotationManager(db)
        
        # Build update dict
        updates = {}
        if title is not None:
            updates['title'] = title
        if content is not None:
            updates['content'] = content
        if color is not None:
            updates['color'] = color
        if is_visible is not None:
            updates['is_visible'] = is_visible
        
        success = annotation_manager.update_annotation(annotation_id, current_user.id, **updates)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Annotation not found or access denied"
            )
        
        return {"message": "Annotation updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating annotation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update annotation: {str(e)}"
        )


@router.delete("/annotations/{annotation_id}")
async def delete_annotation(
    annotation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an annotation."""
    try:
        annotation_manager = AnnotationManager(db)
        
        success = annotation_manager.delete_annotation(annotation_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Annotation not found or access denied"
            )
        
        return {"message": "Annotation deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting annotation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete annotation: {str(e)}"
        )


# Notification Management Endpoints

@router.get("/notifications")
async def get_notifications(
    status: Optional[str] = Query(None, description="Filter by notification status"),
    limit: int = Query(50, description="Maximum number of notifications"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notifications for the current user."""
    try:
        comment_manager = CommentManager(db)
        
        status_filter = None
        if status:
            try:
                status_filter = NotificationStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}"
                )
        
        notifications = comment_manager.get_user_notifications(current_user.id, status_filter)
        
        # Limit results
        notifications = notifications[:limit]
        
        result = []
        for notification in notifications:
            result.append({
                "id": notification.id,
                "comment_id": notification.comment_id,
                "notification_type": notification.notification_type,
                "status": notification.status,
                "content": notification.content,
                "created_at": notification.created_at.isoformat(),
                "read_at": notification.read_at.isoformat() if notification.read_at else None
            })
        
        return {"notifications": result}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notifications: {str(e)}"
        )


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read."""
    try:
        comment_manager = CommentManager(db)
        
        success = comment_manager.mark_notification_read(notification_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return {"message": "Notification marked as read"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification read: {str(e)}"
        )