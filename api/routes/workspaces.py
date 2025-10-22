"""
T036: Real-time Collaboration Features - Workspace API Routes
API endpoints for managing shared project workspaces.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..database import get_db
from ..auth import get_current_user
from ..services.workspace_manager import (
    WorkspaceManager, ProjectManager, WorkspaceRole, 
    WorkspaceSettings, InvitationStatus
)
from ..schemas import User
from ..utils.logger import get_logger

logger = get_logger("workspace_routes")

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])
security = HTTPBearer()


# Workspace Management Endpoints

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    name: str,
    description: str = "",
    settings: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new workspace."""
    try:
        workspace_manager = WorkspaceManager(db)
        
        # Parse settings if provided
        workspace_settings = None
        if settings:
            workspace_settings = WorkspaceSettings(**settings)
        
        workspace = workspace_manager.create_workspace(
            name=name,
            owner_id=current_user.id,
            description=description,
            settings=workspace_settings
        )
        
        return {
            "id": workspace.id,
            "name": workspace.name,
            "description": workspace.description,
            "status": workspace.status,
            "created_at": workspace.created_at.isoformat(),
            "role": "owner"
        }
    
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workspace: {str(e)}"
        )


@router.get("/")
async def get_user_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all workspaces for the current user."""
    try:
        workspace_manager = WorkspaceManager(db)
        workspaces = workspace_manager.get_user_workspaces(current_user.id)
        
        result = []
        for workspace in workspaces:
            role = workspace_manager.get_member_role(workspace.id, current_user.id)
            result.append({
                "id": workspace.id,
                "name": workspace.name,
                "description": workspace.description,
                "status": workspace.status,
                "created_at": workspace.created_at.isoformat(),
                "updated_at": workspace.updated_at.isoformat(),
                "role": role.value if role else None
            })
        
        return {"workspaces": result}
    
    except Exception as e:
        logger.error(f"Error getting user workspaces: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspaces: {str(e)}"
        )


@router.get("/{workspace_id}")
async def get_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workspace details."""
    try:
        workspace_manager = WorkspaceManager(db)
        
        # Check if user has access to workspace
        role = workspace_manager.get_member_role(workspace_id, current_user.id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to workspace"
            )
        
        workspace = workspace_manager.get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        
        # Get workspace statistics
        stats = workspace_manager.get_workspace_stats(workspace_id)
        
        return {
            "id": workspace.id,
            "name": workspace.name,
            "description": workspace.description,
            "status": workspace.status,
            "settings": workspace.settings,
            "created_at": workspace.created_at.isoformat(),
            "updated_at": workspace.updated_at.isoformat(),
            "role": role.value,
            "stats": stats
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workspace {workspace_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace: {str(e)}"
        )


@router.put("/{workspace_id}")
async def update_workspace(
    workspace_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update workspace details."""
    try:
        workspace_manager = WorkspaceManager(db)
        
        # Check permissions
        if not workspace_manager.has_permission(workspace_id, current_user.id, "edit_workspace"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to edit workspace"
            )
        
        workspace = workspace_manager.get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        
        # Update fields
        if name is not None:
            workspace.name = name
        if description is not None:
            workspace.description = description
        if settings is not None:
            workspace.settings = json.dumps(settings)
        
        workspace.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "id": workspace.id,
            "name": workspace.name,
            "description": workspace.description,
            "status": workspace.status,
            "updated_at": workspace.updated_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workspace {workspace_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update workspace: {str(e)}"
        )


# Member Management Endpoints

@router.get("/{workspace_id}/members")
async def get_workspace_members(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all members of a workspace."""
    try:
        workspace_manager = WorkspaceManager(db)
        
        # Check if user has access to workspace
        role = workspace_manager.get_member_role(workspace_id, current_user.id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to workspace"
            )
        
        # Get workspace with members
        workspace = workspace_manager.get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        
        members = []
        for member in workspace.members:
            member_role = workspace_manager.get_member_role(workspace_id, member.id)
            members.append({
                "user_id": member.id,
                "username": member.username,
                "email": member.email,
                "role": member_role.value if member_role else None
            })
        
        return {"members": members}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workspace members: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace members: {str(e)}"
        )


@router.post("/{workspace_id}/invite")
async def invite_user(
    workspace_id: str,
    email: str,
    role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Invite a user to the workspace."""
    try:
        workspace_manager = WorkspaceManager(db)
        
        # Check permissions
        if not workspace_manager.has_permission(workspace_id, current_user.id, "invite_users"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to invite users"
            )
        
        # Validate role
        try:
            workspace_role = WorkspaceRole(role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}"
            )
        
        # Create invitation
        invitation = workspace_manager.create_invitation(
            workspace_id=workspace_id,
            inviter_id=current_user.id,
            invitee_email=email,
            role=workspace_role
        )
        
        return {
            "invitation_id": invitation.id,
            "invitation_token": invitation.invitation_token,
            "email": invitation.invitee_email,
            "role": invitation.role,
            "expires_at": invitation.expires_at.isoformat(),
            "status": invitation.status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inviting user to workspace: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invite user: {str(e)}"
        )


@router.post("/invitations/{invitation_token}/accept")
async def accept_invitation(
    invitation_token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept a workspace invitation."""
    try:
        workspace_manager = WorkspaceManager(db)
        
        success = workspace_manager.accept_invitation(invitation_token, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation"
            )
        
        return {"message": "Invitation accepted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept invitation: {str(e)}"
        )


@router.put("/{workspace_id}/members/{user_id}/role")
async def update_member_role(
    workspace_id: str,
    user_id: int,
    new_role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a member's role in the workspace."""
    try:
        workspace_manager = WorkspaceManager(db)
        
        # Check permissions
        if not workspace_manager.has_permission(workspace_id, current_user.id, "manage_members"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to manage members"
            )
        
        # Validate role
        try:
            workspace_role = WorkspaceRole(new_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {new_role}"
            )
        
        # Prevent owner from changing their own role
        if (user_id == current_user.id and 
            workspace_manager.get_member_role(workspace_id, current_user.id) == WorkspaceRole.OWNER):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Owner cannot change their own role"
            )
        
        success = workspace_manager.update_member_role(workspace_id, user_id, workspace_role)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a member of this workspace"
            )
        
        return {"message": "Member role updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating member role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update member role: {str(e)}"
        )


@router.delete("/{workspace_id}/members/{user_id}")
async def remove_member(
    workspace_id: str,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a member from the workspace."""
    try:
        workspace_manager = WorkspaceManager(db)
        
        # Check permissions
        if not workspace_manager.has_permission(workspace_id, current_user.id, "manage_members"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to manage members"
            )
        
        # Prevent owner from removing themselves
        if (user_id == current_user.id and 
            workspace_manager.get_member_role(workspace_id, current_user.id) == WorkspaceRole.OWNER):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Owner cannot remove themselves from workspace"
            )
        
        success = workspace_manager.remove_member(workspace_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a member of this workspace"
            )
        
        return {"message": "Member removed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove member: {str(e)}"
        )


# Project Management Endpoints

@router.get("/{workspace_id}/projects")
async def get_workspace_projects(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all projects in a workspace."""
    try:
        workspace_manager = WorkspaceManager(db)
        project_manager = ProjectManager(db)
        
        # Check access
        role = workspace_manager.get_member_role(workspace_id, current_user.id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to workspace"
            )
        
        projects = project_manager.get_workspace_projects(workspace_id)
        
        result = []
        for project in projects:
            result.append({
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "project_type": project.project_type,
                "status": project.status,
                "created_by": project.created_by,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat()
            })
        
        return {"projects": result}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workspace projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get projects: {str(e)}"
        )


@router.post("/{workspace_id}/projects")
async def create_project(
    workspace_id: str,
    name: str,
    description: str = "",
    project_type: str = "transcription",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project in the workspace."""
    try:
        workspace_manager = WorkspaceManager(db)
        project_manager = ProjectManager(db)
        
        # Check permissions
        if not workspace_manager.has_permission(workspace_id, current_user.id, "create_projects"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create projects"
            )
        
        project = project_manager.create_project(
            workspace_id=workspace_id,
            name=name,
            creator_id=current_user.id,
            description=description,
            project_type=project_type
        )
        
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "project_type": project.project_type,
            "status": project.status,
            "created_at": project.created_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.get("/{workspace_id}/projects/{project_id}/documents")
async def get_project_documents(
    workspace_id: str,
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all documents in a project."""
    try:
        workspace_manager = WorkspaceManager(db)
        project_manager = ProjectManager(db)
        
        # Check access
        role = workspace_manager.get_member_role(workspace_id, current_user.id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to workspace"
            )
        
        # Verify project belongs to workspace
        project = project_manager.get_project(project_id)
        if not project or project.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        documents = project_manager.get_project_documents(project_id)
        
        result = []
        for document in documents:
            result.append({
                "id": document.id,
                "name": document.name,
                "document_type": document.document_type,
                "version": document.version,
                "created_by": document.created_by,
                "created_at": document.created_at.isoformat(),
                "updated_at": document.updated_at.isoformat()
            })
        
        return {"documents": result}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents: {str(e)}"
        )


@router.post("/{workspace_id}/projects/{project_id}/documents")
async def create_document(
    workspace_id: str,
    project_id: str,
    name: str,
    content: str = "",
    document_type: str = "transcript",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new document in the project."""
    try:
        workspace_manager = WorkspaceManager(db)
        project_manager = ProjectManager(db)
        
        # Check permissions
        if not workspace_manager.has_permission(workspace_id, current_user.id, "edit_projects"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create documents"
            )
        
        # Verify project belongs to workspace
        project = project_manager.get_project(project_id)
        if not project or project.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        document = project_manager.create_document(
            project_id=project_id,
            name=name,
            creator_id=current_user.id,
            content=content,
            document_type=document_type
        )
        
        return {
            "id": document.id,
            "name": document.name,
            "document_type": document.document_type,
            "version": document.version,
            "created_at": document.created_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}"
        )


@router.get("/stats")
async def get_workspace_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workspace statistics for the current user."""
    try:
        workspace_manager = WorkspaceManager(db)
        user_workspaces = workspace_manager.get_user_workspaces(current_user.id)
        
        total_workspaces = len(user_workspaces)
        total_projects = 0
        
        workspace_details = []
        for workspace in user_workspaces:
            stats = workspace_manager.get_workspace_stats(workspace.id)
            workspace_details.append(stats)
            total_projects += stats.get("project_count", 0)
        
        return {
            "total_workspaces": total_workspaces,
            "total_projects": total_projects,
            "workspaces": workspace_details
        }
    
    except Exception as e:
        logger.error(f"Error getting workspace stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace stats: {str(e)}"
        )