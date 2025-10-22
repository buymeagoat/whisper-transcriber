"""
T036: Real-time Collaboration Features - Shared Project Workspaces
Implements workspace management for collaborative transcription projects.
"""

import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass, asdict
from uuid import uuid4

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declarative_base

from ..models import Base
from ..utils.logger import get_logger

logger = get_logger("shared_workspaces")


class WorkspaceRole(Enum):
    """User roles within a workspace."""
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    GUEST = "guest"


class WorkspaceStatus(Enum):
    """Workspace status states."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    SUSPENDED = "suspended"


class InvitationStatus(Enum):
    """Invitation status states."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


# Association table for workspace members
workspace_members = Table(
    'workspace_members',
    Base.metadata,
    Column('workspace_id', String, ForeignKey('workspaces.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role', String, nullable=False),
    Column('joined_at', DateTime(timezone=True), default=datetime.utcnow),
    Column('last_active', DateTime(timezone=True), default=datetime.utcnow)
)


class Workspace(Base):
    """Database model for collaborative workspaces."""
    
    __tablename__ = 'workspaces'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(20), default=WorkspaceStatus.ACTIVE.value)
    settings = Column(Text)  # JSON string for workspace settings
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("User", secondary=workspace_members, back_populates="workspaces")
    projects = relationship("WorkspaceProject", back_populates="workspace")
    invitations = relationship("WorkspaceInvitation", back_populates="workspace")


class WorkspaceProject(Base):
    """Database model for projects within workspaces."""
    
    __tablename__ = 'workspace_projects'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    workspace_id = Column(String, ForeignKey('workspaces.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    project_type = Column(String(50), default='transcription')  # transcription, analysis, etc.
    settings = Column(Text)  # JSON string for project settings
    metadata = Column(Text)  # JSON string for project metadata
    status = Column(String(20), default='active')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="projects")
    creator = relationship("User", foreign_keys=[created_by])
    documents = relationship("ProjectDocument", back_populates="project")


class ProjectDocument(Base):
    """Database model for documents within workspace projects."""
    
    __tablename__ = 'project_documents'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String, ForeignKey('workspace_projects.id'), nullable=False)
    name = Column(String(255), nullable=False)
    document_type = Column(String(50), default='transcript')  # transcript, analysis, notes
    content = Column(Text)
    metadata = Column(Text)  # JSON string for document metadata
    version = Column(Integer, default=1)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("WorkspaceProject", back_populates="documents")
    creator = relationship("User", foreign_keys=[created_by])


class WorkspaceInvitation(Base):
    """Database model for workspace invitations."""
    
    __tablename__ = 'workspace_invitations'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    workspace_id = Column(String, ForeignKey('workspaces.id'), nullable=False)
    inviter_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    invitee_email = Column(String(255), nullable=False)
    invitee_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Set when user accepts
    role = Column(String(20), nullable=False)
    status = Column(String(20), default=InvitationStatus.PENDING.value)
    invitation_token = Column(String(255), unique=True, default=lambda: str(uuid4()))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    accepted_at = Column(DateTime(timezone=True))
    
    # Relationships
    workspace = relationship("Workspace", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[inviter_id])
    invitee = relationship("User", foreign_keys=[invitee_id])


@dataclass
class WorkspaceSettings:
    """Configuration settings for a workspace."""
    max_members: int = 50
    allow_guest_access: bool = False
    require_approval: bool = True
    default_project_permissions: Dict[str, bool] = None
    collaboration_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.default_project_permissions is None:
            self.default_project_permissions = {
                "create_projects": True,
                "edit_projects": True,
                "delete_projects": False,
                "invite_users": False
            }
        
        if self.collaboration_settings is None:
            self.collaboration_settings = {
                "real_time_editing": True,
                "comments_enabled": True,
                "version_history": True,
                "auto_save_interval": 30
            }


class WorkspaceManager:
    """Manages workspace operations and permissions."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_workspace(self, name: str, owner_id: int, description: str = "",
                        settings: Optional[WorkspaceSettings] = None) -> Workspace:
        """
        Create a new workspace.
        
        Args:
            name: Workspace name
            owner_id: ID of the workspace owner
            description: Workspace description
            settings: Workspace configuration settings
            
        Returns:
            Created workspace
        """
        try:
            if settings is None:
                settings = WorkspaceSettings()
            
            workspace = Workspace(
                name=name,
                description=description,
                owner_id=owner_id,
                settings=json.dumps(asdict(settings))
            )
            
            self.db.add(workspace)
            self.db.commit()
            self.db.refresh(workspace)
            
            # Add owner as a member with OWNER role
            self.add_member(workspace.id, owner_id, WorkspaceRole.OWNER)
            
            logger.info(f"Created workspace {workspace.id} for user {owner_id}")
            return workspace
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating workspace: {e}")
            raise
    
    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get workspace by ID."""
        return self.db.query(Workspace).filter(
            Workspace.id == workspace_id,
            Workspace.status != WorkspaceStatus.DELETED.value
        ).first()
    
    def get_user_workspaces(self, user_id: int) -> List[Workspace]:
        """Get all workspaces for a user."""
        return self.db.query(Workspace).join(workspace_members).filter(
            workspace_members.c.user_id == user_id,
            Workspace.status == WorkspaceStatus.ACTIVE.value
        ).all()
    
    def add_member(self, workspace_id: str, user_id: int, role: WorkspaceRole) -> bool:
        """
        Add a member to a workspace.
        
        Args:
            workspace_id: Workspace ID
            user_id: User ID
            role: User role in the workspace
            
        Returns:
            True if member was added successfully
        """
        try:
            # Check if user is already a member
            existing = self.db.execute(
                workspace_members.select().where(
                    workspace_members.c.workspace_id == workspace_id,
                    workspace_members.c.user_id == user_id
                )
            ).first()
            
            if existing:
                logger.warning(f"User {user_id} is already a member of workspace {workspace_id}")
                return False
            
            # Add new member
            self.db.execute(
                workspace_members.insert().values(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    role=role.value
                )
            )
            self.db.commit()
            
            logger.info(f"Added user {user_id} to workspace {workspace_id} with role {role.value}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding member to workspace: {e}")
            return False
    
    def remove_member(self, workspace_id: str, user_id: int) -> bool:
        """Remove a member from a workspace."""
        try:
            result = self.db.execute(
                workspace_members.delete().where(
                    workspace_members.c.workspace_id == workspace_id,
                    workspace_members.c.user_id == user_id
                )
            )
            self.db.commit()
            
            if result.rowcount > 0:
                logger.info(f"Removed user {user_id} from workspace {workspace_id}")
                return True
            else:
                logger.warning(f"User {user_id} was not a member of workspace {workspace_id}")
                return False
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing member from workspace: {e}")
            return False
    
    def update_member_role(self, workspace_id: str, user_id: int, new_role: WorkspaceRole) -> bool:
        """Update a member's role in a workspace."""
        try:
            result = self.db.execute(
                workspace_members.update().where(
                    workspace_members.c.workspace_id == workspace_id,
                    workspace_members.c.user_id == user_id
                ).values(role=new_role.value)
            )
            self.db.commit()
            
            if result.rowcount > 0:
                logger.info(f"Updated user {user_id} role to {new_role.value} in workspace {workspace_id}")
                return True
            else:
                logger.warning(f"User {user_id} is not a member of workspace {workspace_id}")
                return False
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating member role: {e}")
            return False
    
    def get_member_role(self, workspace_id: str, user_id: int) -> Optional[WorkspaceRole]:
        """Get a user's role in a workspace."""
        result = self.db.execute(
            workspace_members.select().where(
                workspace_members.c.workspace_id == workspace_id,
                workspace_members.c.user_id == user_id
            )
        ).first()
        
        if result:
            return WorkspaceRole(result.role)
        return None
    
    def has_permission(self, workspace_id: str, user_id: int, permission: str) -> bool:
        """
        Check if a user has a specific permission in a workspace.
        
        Args:
            workspace_id: Workspace ID
            user_id: User ID
            permission: Permission to check
            
        Returns:
            True if user has the permission
        """
        role = self.get_member_role(workspace_id, user_id)
        if not role:
            return False
        
        # Define permission matrix
        permissions = {
            WorkspaceRole.OWNER: ["all"],
            WorkspaceRole.ADMIN: [
                "manage_members", "create_projects", "edit_projects", 
                "delete_projects", "invite_users", "edit_workspace"
            ],
            WorkspaceRole.EDITOR: [
                "create_projects", "edit_projects", "edit_documents"
            ],
            WorkspaceRole.VIEWER: [
                "view_projects", "view_documents"
            ],
            WorkspaceRole.GUEST: [
                "view_projects"
            ]
        }
        
        user_permissions = permissions.get(role, [])
        return "all" in user_permissions or permission in user_permissions
    
    def create_invitation(self, workspace_id: str, inviter_id: int, 
                         invitee_email: str, role: WorkspaceRole,
                         expires_days: int = 7) -> WorkspaceInvitation:
        """Create a workspace invitation."""
        try:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
            
            invitation = WorkspaceInvitation(
                workspace_id=workspace_id,
                inviter_id=inviter_id,
                invitee_email=invitee_email,
                role=role.value,
                expires_at=expires_at
            )
            
            self.db.add(invitation)
            self.db.commit()
            self.db.refresh(invitation)
            
            logger.info(f"Created invitation for {invitee_email} to workspace {workspace_id}")
            return invitation
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating invitation: {e}")
            raise
    
    def accept_invitation(self, invitation_token: str, user_id: int) -> bool:
        """Accept a workspace invitation."""
        try:
            invitation = self.db.query(WorkspaceInvitation).filter(
                WorkspaceInvitation.invitation_token == invitation_token,
                WorkspaceInvitation.status == InvitationStatus.PENDING.value,
                WorkspaceInvitation.expires_at > datetime.now(timezone.utc)
            ).first()
            
            if not invitation:
                logger.warning(f"Invalid or expired invitation token: {invitation_token}")
                return False
            
            # Add user to workspace
            role = WorkspaceRole(invitation.role)
            if self.add_member(invitation.workspace_id, user_id, role):
                # Update invitation status
                invitation.status = InvitationStatus.ACCEPTED.value
                invitation.invitee_id = user_id
                invitation.accepted_at = datetime.now(timezone.utc)
                self.db.commit()
                
                logger.info(f"User {user_id} accepted invitation to workspace {invitation.workspace_id}")
                return True
            
            return False
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error accepting invitation: {e}")
            return False
    
    def get_workspace_stats(self, workspace_id: str) -> Dict[str, Any]:
        """Get workspace statistics."""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return {}
        
        member_count = self.db.execute(
            workspace_members.select().where(
                workspace_members.c.workspace_id == workspace_id
            )
        ).rowcount
        
        project_count = self.db.query(WorkspaceProject).filter(
            WorkspaceProject.workspace_id == workspace_id,
            WorkspaceProject.status == 'active'
        ).count()
        
        return {
            "workspace_id": workspace_id,
            "name": workspace.name,
            "status": workspace.status,
            "member_count": member_count,
            "project_count": project_count,
            "created_at": workspace.created_at.isoformat(),
            "updated_at": workspace.updated_at.isoformat()
        }


class ProjectManager:
    """Manages workspace projects and documents."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_project(self, workspace_id: str, name: str, creator_id: int,
                      description: str = "", project_type: str = "transcription") -> WorkspaceProject:
        """Create a new project in a workspace."""
        try:
            project = WorkspaceProject(
                workspace_id=workspace_id,
                name=name,
                description=description,
                project_type=project_type,
                created_by=creator_id
            )
            
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
            
            logger.info(f"Created project {project.id} in workspace {workspace_id}")
            return project
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating project: {e}")
            raise
    
    def get_project(self, project_id: str) -> Optional[WorkspaceProject]:
        """Get project by ID."""
        return self.db.query(WorkspaceProject).filter(
            WorkspaceProject.id == project_id,
            WorkspaceProject.status == 'active'
        ).first()
    
    def get_workspace_projects(self, workspace_id: str) -> List[WorkspaceProject]:
        """Get all projects in a workspace."""
        return self.db.query(WorkspaceProject).filter(
            WorkspaceProject.workspace_id == workspace_id,
            WorkspaceProject.status == 'active'
        ).all()
    
    def create_document(self, project_id: str, name: str, creator_id: int,
                       content: str = "", document_type: str = "transcript") -> ProjectDocument:
        """Create a new document in a project."""
        try:
            document = ProjectDocument(
                project_id=project_id,
                name=name,
                document_type=document_type,
                content=content,
                created_by=creator_id
            )
            
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            logger.info(f"Created document {document.id} in project {project_id}")
            return document
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating document: {e}")
            raise
    
    def get_document(self, document_id: str) -> Optional[ProjectDocument]:
        """Get document by ID."""
        return self.db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()
    
    def get_project_documents(self, project_id: str) -> List[ProjectDocument]:
        """Get all documents in a project."""
        return self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()
    
    def update_document_content(self, document_id: str, content: str, user_id: int) -> bool:
        """Update document content."""
        try:
            document = self.get_document(document_id)
            if not document:
                return False
            
            document.content = content
            document.version += 1
            document.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"Updated document {document_id} (version {document.version})")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating document: {e}")
            return False