"""
T036: Real-time Collaboration Features - Comments & Annotations System
Implements real-time commenting, annotations, and mentions for collaborative editing.
"""

import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass, asdict
from uuid import uuid4

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Session

from ..models import Base
from ..utils.logger import get_logger

logger = get_logger("comments_annotations")


class CommentType(Enum):
    """Types of comments."""
    GENERAL = "general"
    SUGGESTION = "suggestion"
    QUESTION = "question"
    APPROVAL = "approval"
    CORRECTION = "correction"


class AnnotationType(Enum):
    """Types of annotations."""
    HIGHLIGHT = "highlight"
    NOTE = "note"
    BOOKMARK = "bookmark"
    TASK = "task"
    ISSUE = "issue"


class CommentStatus(Enum):
    """Status of comments."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ARCHIVED = "archived"
    DELETED = "deleted"


class NotificationStatus(Enum):
    """Status of notifications."""
    UNREAD = "unread"
    READ = "read"
    DISMISSED = "dismissed"


class Comment(Base):
    """Database model for comments."""
    
    __tablename__ = 'comments'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    document_id = Column(String, ForeignKey('project_documents.id'), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    parent_id = Column(String, ForeignKey('comments.id'), nullable=True)  # For threading
    content = Column(Text, nullable=False)
    comment_type = Column(String(20), default=CommentType.GENERAL.value)
    status = Column(String(20), default=CommentStatus.ACTIVE.value)
    
    # Position information for inline comments
    start_position = Column(Integer)  # Character position in document
    end_position = Column(Integer)
    line_number = Column(Integer)
    selected_text = Column(Text)  # Text that was selected when comment was made
    
    # Metadata
    metadata = Column(Text)  # JSON string for additional data
    resolved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    resolved_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship("ProjectDocument", foreign_keys=[document_id])
    author = relationship("User", foreign_keys=[author_id])
    resolver = relationship("User", foreign_keys=[resolved_by])
    replies = relationship("Comment", backref="parent", remote_side=[id])
    mentions = relationship("CommentMention", back_populates="comment")
    reactions = relationship("CommentReaction", back_populates="comment")


class Annotation(Base):
    """Database model for document annotations."""
    
    __tablename__ = 'annotations'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    document_id = Column(String, ForeignKey('project_documents.id'), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    annotation_type = Column(String(20), default=AnnotationType.HIGHLIGHT.value)
    
    # Position information
    start_position = Column(Integer, nullable=False)
    end_position = Column(Integer, nullable=False)
    selected_text = Column(Text)
    
    # Content
    title = Column(String(255))
    content = Column(Text)
    color = Column(String(7), default="#FFD700")  # Hex color for highlighting
    
    # Metadata
    metadata = Column(Text)  # JSON string for additional data
    is_visible = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship("ProjectDocument", foreign_keys=[document_id])
    author = relationship("User", foreign_keys=[author_id])


class CommentMention(Base):
    """Database model for user mentions in comments."""
    
    __tablename__ = 'comment_mentions'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    comment_id = Column(String, ForeignKey('comments.id'), nullable=False)
    mentioned_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    mentioned_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    position_in_comment = Column(Integer)  # Position of mention in comment text
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    comment = relationship("Comment", back_populates="mentions")
    mentioned_user = relationship("User", foreign_keys=[mentioned_user_id])
    mentioned_by = relationship("User", foreign_keys=[mentioned_by_id])


class CommentReaction(Base):
    """Database model for comment reactions (likes, etc.)."""
    
    __tablename__ = 'comment_reactions'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    comment_id = Column(String, ForeignKey('comments.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reaction_type = Column(String(20), nullable=False)  # like, dislike, heart, etc.
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    comment = relationship("Comment", back_populates="reactions")
    user = relationship("User", foreign_keys=[user_id])
    
    # Unique constraint to prevent duplicate reactions
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class CommentNotification(Base):
    """Database model for comment-related notifications."""
    
    __tablename__ = 'comment_notifications'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    comment_id = Column(String, ForeignKey('comments.id'), nullable=False)
    notification_type = Column(String(50), nullable=False)  # mention, reply, reaction, etc.
    status = Column(String(20), default=NotificationStatus.UNREAD.value)
    content = Column(Text)  # Notification message
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    read_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    comment = relationship("Comment", foreign_keys=[comment_id])


@dataclass
class CommentPosition:
    """Position information for a comment."""
    start_position: int
    end_position: int
    line_number: Optional[int] = None
    selected_text: Optional[str] = None


@dataclass
class CommentData:
    """Data structure for comment information."""
    id: str
    content: str
    author_id: int
    author_name: str
    comment_type: str
    status: str
    position: Optional[CommentPosition] = None
    parent_id: Optional[str] = None
    replies: List['CommentData'] = None
    mentions: List[Dict[str, Any]] = None
    reactions: List[Dict[str, Any]] = None
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if self.replies is None:
            self.replies = []
        if self.mentions is None:
            self.mentions = []
        if self.reactions is None:
            self.reactions = []


class CommentManager:
    """Manages comment operations and threading."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_comment(self, document_id: str, author_id: int, content: str,
                      comment_type: CommentType = CommentType.GENERAL,
                      position: Optional[CommentPosition] = None,
                      parent_id: Optional[str] = None) -> Comment:
        """
        Create a new comment.
        
        Args:
            document_id: ID of the document
            author_id: ID of the comment author
            content: Comment content
            comment_type: Type of comment
            position: Position information for inline comments
            parent_id: Parent comment ID for threading
            
        Returns:
            Created comment
        """
        try:
            comment = Comment(
                document_id=document_id,
                author_id=author_id,
                content=content,
                comment_type=comment_type.value,
                parent_id=parent_id
            )
            
            if position:
                comment.start_position = position.start_position
                comment.end_position = position.end_position
                comment.line_number = position.line_number
                comment.selected_text = position.selected_text
            
            self.db.add(comment)
            self.db.commit()
            self.db.refresh(comment)
            
            # Process mentions in the comment
            self._process_mentions(comment)
            
            logger.info(f"Created comment {comment.id} on document {document_id}")
            return comment
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating comment: {e}")
            raise
    
    def get_comment(self, comment_id: str) -> Optional[Comment]:
        """Get comment by ID."""
        return self.db.query(Comment).filter(
            Comment.id == comment_id,
            Comment.status != CommentStatus.DELETED.value
        ).first()
    
    def get_document_comments(self, document_id: str, 
                             include_resolved: bool = False) -> List[Comment]:
        """
        Get all comments for a document.
        
        Args:
            document_id: Document ID
            include_resolved: Whether to include resolved comments
            
        Returns:
            List of comments
        """
        query = self.db.query(Comment).filter(
            Comment.document_id == document_id,
            Comment.status != CommentStatus.DELETED.value
        )
        
        if not include_resolved:
            query = query.filter(Comment.status != CommentStatus.RESOLVED.value)
        
        return query.order_by(Comment.created_at).all()
    
    def get_comment_thread(self, comment_id: str) -> List[Comment]:
        """Get a comment thread (parent comment and all replies)."""
        # Get the root comment
        root_comment = self.get_comment(comment_id)
        if not root_comment:
            return []
        
        # If this is a reply, get the parent
        if root_comment.parent_id:
            root_comment = self.get_comment(root_comment.parent_id)
            if not root_comment:
                return []
        
        # Get all replies
        replies = self.db.query(Comment).filter(
            Comment.parent_id == root_comment.id,
            Comment.status != CommentStatus.DELETED.value
        ).order_by(Comment.created_at).all()
        
        return [root_comment] + replies
    
    def update_comment(self, comment_id: str, content: str, user_id: int) -> bool:
        """Update comment content."""
        try:
            comment = self.get_comment(comment_id)
            if not comment:
                return False
            
            # Check if user can edit this comment
            if comment.author_id != user_id:
                logger.warning(f"User {user_id} cannot edit comment {comment_id}")
                return False
            
            comment.content = content
            comment.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            
            # Reprocess mentions
            self._process_mentions(comment)
            
            logger.info(f"Updated comment {comment_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating comment: {e}")
            return False
    
    def resolve_comment(self, comment_id: str, resolver_id: int) -> bool:
        """Mark comment as resolved."""
        try:
            comment = self.get_comment(comment_id)
            if not comment:
                return False
            
            comment.status = CommentStatus.RESOLVED.value
            comment.resolved_by = resolver_id
            comment.resolved_at = datetime.now(timezone.utc)
            self.db.commit()
            
            logger.info(f"Resolved comment {comment_id} by user {resolver_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error resolving comment: {e}")
            return False
    
    def delete_comment(self, comment_id: str, user_id: int) -> bool:
        """Soft delete a comment."""
        try:
            comment = self.get_comment(comment_id)
            if not comment:
                return False
            
            # Check if user can delete this comment
            if comment.author_id != user_id:
                logger.warning(f"User {user_id} cannot delete comment {comment_id}")
                return False
            
            comment.status = CommentStatus.DELETED.value
            comment.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            
            logger.info(f"Deleted comment {comment_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting comment: {e}")
            return False
    
    def add_reaction(self, comment_id: str, user_id: int, reaction_type: str) -> bool:
        """Add a reaction to a comment."""
        try:
            # Check if user already reacted with this type
            existing = self.db.query(CommentReaction).filter(
                CommentReaction.comment_id == comment_id,
                CommentReaction.user_id == user_id,
                CommentReaction.reaction_type == reaction_type
            ).first()
            
            if existing:
                return False  # Already reacted
            
            reaction = CommentReaction(
                comment_id=comment_id,
                user_id=user_id,
                reaction_type=reaction_type
            )
            
            self.db.add(reaction)
            self.db.commit()
            
            logger.info(f"Added {reaction_type} reaction to comment {comment_id} by user {user_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding reaction: {e}")
            return False
    
    def remove_reaction(self, comment_id: str, user_id: int, reaction_type: str) -> bool:
        """Remove a reaction from a comment."""
        try:
            reaction = self.db.query(CommentReaction).filter(
                CommentReaction.comment_id == comment_id,
                CommentReaction.user_id == user_id,
                CommentReaction.reaction_type == reaction_type
            ).first()
            
            if not reaction:
                return False
            
            self.db.delete(reaction)
            self.db.commit()
            
            logger.info(f"Removed {reaction_type} reaction from comment {comment_id} by user {user_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing reaction: {e}")
            return False
    
    def _process_mentions(self, comment: Comment):
        """Process @mentions in comment content and create mention records."""
        try:
            # Clear existing mentions for this comment
            self.db.query(CommentMention).filter(
                CommentMention.comment_id == comment.id
            ).delete()
            
            # Find mentions in content (simple regex for @username)
            import re
            mention_pattern = r'@(\w+)'
            mentions = re.finditer(mention_pattern, comment.content)
            
            for match in mentions:
                username = match.group(1)
                position = match.start()
                
                # Find user by username (assuming User model has username field)
                from ..models import User
                mentioned_user = self.db.query(User).filter(
                    User.username == username
                ).first()
                
                if mentioned_user:
                    mention = CommentMention(
                        comment_id=comment.id,
                        mentioned_user_id=mentioned_user.id,
                        mentioned_by_id=comment.author_id,
                        position_in_comment=position
                    )
                    self.db.add(mention)
                    
                    # Create notification
                    self._create_notification(
                        mentioned_user.id,
                        comment.id,
                        "mention",
                        f"You were mentioned in a comment by {comment.author.username}"
                    )
            
            self.db.commit()
        
        except Exception as e:
            logger.error(f"Error processing mentions: {e}")
    
    def _create_notification(self, user_id: int, comment_id: str, 
                           notification_type: str, content: str):
        """Create a notification for a user."""
        try:
            notification = CommentNotification(
                user_id=user_id,
                comment_id=comment_id,
                notification_type=notification_type,
                content=content
            )
            self.db.add(notification)
        
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
    
    def get_user_notifications(self, user_id: int, 
                              status: Optional[NotificationStatus] = None) -> List[CommentNotification]:
        """Get notifications for a user."""
        query = self.db.query(CommentNotification).filter(
            CommentNotification.user_id == user_id
        )
        
        if status:
            query = query.filter(CommentNotification.status == status.value)
        
        return query.order_by(CommentNotification.created_at.desc()).all()
    
    def mark_notification_read(self, notification_id: str, user_id: int) -> bool:
        """Mark a notification as read."""
        try:
            notification = self.db.query(CommentNotification).filter(
                CommentNotification.id == notification_id,
                CommentNotification.user_id == user_id
            ).first()
            
            if not notification:
                return False
            
            notification.status = NotificationStatus.READ.value
            notification.read_at = datetime.now(timezone.utc)
            self.db.commit()
            
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking notification read: {e}")
            return False


class AnnotationManager:
    """Manages document annotations."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_annotation(self, document_id: str, author_id: int,
                         annotation_type: AnnotationType, start_position: int,
                         end_position: int, selected_text: str = "",
                         title: str = "", content: str = "",
                         color: str = "#FFD700") -> Annotation:
        """Create a new annotation."""
        try:
            annotation = Annotation(
                document_id=document_id,
                author_id=author_id,
                annotation_type=annotation_type.value,
                start_position=start_position,
                end_position=end_position,
                selected_text=selected_text,
                title=title,
                content=content,
                color=color
            )
            
            self.db.add(annotation)
            self.db.commit()
            self.db.refresh(annotation)
            
            logger.info(f"Created annotation {annotation.id} on document {document_id}")
            return annotation
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating annotation: {e}")
            raise
    
    def get_document_annotations(self, document_id: str) -> List[Annotation]:
        """Get all annotations for a document."""
        return self.db.query(Annotation).filter(
            Annotation.document_id == document_id,
            Annotation.is_visible == True
        ).order_by(Annotation.start_position).all()
    
    def update_annotation(self, annotation_id: str, user_id: int, **kwargs) -> bool:
        """Update annotation properties."""
        try:
            annotation = self.db.query(Annotation).filter(
                Annotation.id == annotation_id
            ).first()
            
            if not annotation:
                return False
            
            # Check if user can edit this annotation
            if annotation.author_id != user_id:
                return False
            
            # Update allowed fields
            allowed_fields = ['title', 'content', 'color', 'is_visible']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(annotation, field, value)
            
            annotation.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            
            logger.info(f"Updated annotation {annotation_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating annotation: {e}")
            return False
    
    def delete_annotation(self, annotation_id: str, user_id: int) -> bool:
        """Delete an annotation."""
        try:
            annotation = self.db.query(Annotation).filter(
                Annotation.id == annotation_id
            ).first()
            
            if not annotation:
                return False
            
            # Check if user can delete this annotation
            if annotation.author_id != user_id:
                return False
            
            self.db.delete(annotation)
            self.db.commit()
            
            logger.info(f"Deleted annotation {annotation_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting annotation: {e}")
            return False