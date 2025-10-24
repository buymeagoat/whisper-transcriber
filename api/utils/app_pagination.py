"""
Pagination utilities for the Whisper Transcriber API.

This module provides cursor-based pagination for efficient handling of large datasets
with support for total counts, configurable page sizes, and navigation metadata.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Generic, TypeVar, Union
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session, Query
from sqlalchemy import desc, asc, func, and_, or_
import base64
import json

from api.schemas_app import BaseSchema, ValidationConfig, sanitize_string

# Generic type for paginated data
T = TypeVar('T')


class PaginationConfig:
    """Configuration for pagination limits and defaults."""
    
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    MIN_PAGE_SIZE = 1
    MAX_CURSOR_AGE_HOURS = 24


class PaginationRequest(BaseSchema):
    """Request schema for pagination parameters."""
    
    page_size: Optional[int] = Field(
        default=PaginationConfig.DEFAULT_PAGE_SIZE,
        ge=PaginationConfig.MIN_PAGE_SIZE,
        le=PaginationConfig.MAX_PAGE_SIZE,
        description=f"Number of items per page ({PaginationConfig.MIN_PAGE_SIZE}-{PaginationConfig.MAX_PAGE_SIZE})"
    )
    cursor: Optional[str] = Field(
        None,
        max_length=500,
        description="Pagination cursor for next/previous page"
    )
    sort_by: Optional[str] = Field(
        default="created_at",
        max_length=50,
        description="Field to sort by"
    )
    sort_order: Optional[str] = Field(
        default="desc",
        description="Sort order: 'asc' or 'desc'"
    )
    include_total: Optional[bool] = Field(
        default=False,
        description="Include total count in response (may impact performance)"
    )
    
    @field_validator('cursor')
    @classmethod
    def validate_cursor(cls, v: Optional[str]) -> Optional[str]:
        """Validate and decode pagination cursor."""
        if v is None:
            return v
            
        v = sanitize_string(v)
        
        try:
            # Decode and validate cursor format
            decoded = base64.b64decode(v).decode('utf-8')
            cursor_data = json.loads(decoded)
            
            # Validate required cursor fields
            required_fields = ['timestamp', 'id', 'sort_by', 'sort_order']
            if not all(field in cursor_data for field in required_fields):
                raise ValueError("Invalid cursor format")
                
            # Validate cursor age (prevent replay attacks)
            cursor_time = datetime.fromisoformat(cursor_data['timestamp'])
            age_hours = (datetime.utcnow() - cursor_time).total_seconds() / 3600
            if age_hours > PaginationConfig.MAX_CURSOR_AGE_HOURS:
                raise ValueError("Cursor expired")
                
            return v
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            raise ValueError("Invalid cursor format")
    
    @field_validator('sort_by')
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """Validate sort field."""
        v = sanitize_string(v)
        
        # Allowlist of sortable fields
        allowed_fields = [
            'created_at', 'completed_at', 'filename', 'status', 
            'model_used', 'file_size', 'duration'
        ]
        
        if v not in allowed_fields:
            raise ValueError(f"Invalid sort field. Must be one of: {', '.join(allowed_fields)}")
            
        return v
    
    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate sort order."""
        v = sanitize_string(v).lower()
        
        if v not in ['asc', 'desc']:
            raise ValueError("Sort order must be 'asc' or 'desc'")
            
        return v


class PaginationMetadata(BaseModel):
    """Pagination metadata for response."""
    
    page_size: int = Field(..., description="Number of items per page")
    total_count: Optional[int] = Field(None, description="Total number of items")
    has_next: bool = Field(..., description="Whether there are more items")
    has_previous: bool = Field(..., description="Whether there are previous items")
    next_cursor: Optional[str] = Field(None, description="Cursor for next page")
    previous_cursor: Optional[str] = Field(None, description="Cursor for previous page")
    sort_by: str = Field(..., description="Field used for sorting")
    sort_order: str = Field(..., description="Sort order applied")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    
    data: List[T] = Field(..., description="Paginated data items")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")


class CursorGenerator:
    """Utility for generating and parsing pagination cursors."""
    
    @staticmethod
    def generate_cursor(
        item_id: str,
        sort_field_value: Any,
        sort_by: str,
        sort_order: str
    ) -> str:
        """Generate a cursor for pagination."""
        cursor_data = {
            'id': item_id,
            'sort_value': str(sort_field_value) if sort_field_value is not None else None,
            'sort_by': sort_by,
            'sort_order': sort_order,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        cursor_json = json.dumps(cursor_data, separators=(',', ':'))
        cursor_b64 = base64.b64encode(cursor_json.encode('utf-8')).decode('utf-8')
        
        return cursor_b64
    
    @staticmethod
    def parse_cursor(cursor: str) -> Dict[str, Any]:
        """Parse a pagination cursor."""
        try:
            decoded = base64.b64decode(cursor).decode('utf-8')
            return json.loads(decoded)
        except (json.JSONDecodeError, ValueError, KeyError):
            raise ValueError("Invalid cursor format")


class JobPaginator:
    """Pagination handler for Job queries."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def paginate_jobs(
        self,
        base_query: Query,
        pagination: PaginationRequest,
        user_id: Optional[str] = None
    ) -> PaginatedResponse:
        """
        Paginate job results with cursor-based navigation.
        
        Args:
            base_query: Base SQLAlchemy query to paginate
            pagination: Pagination parameters
            user_id: Optional user ID for filtering (not implemented in current schema)
        
        Returns:
            PaginatedResponse with jobs and pagination metadata
        """
        from api.models import Job  # Import here to avoid circular imports
        
        # Apply sorting
        sort_column = getattr(Job, pagination.sort_by)
        if pagination.sort_order == 'desc':
            base_query = base_query.order_by(desc(sort_column), desc(Job.id))
        else:
            base_query = base_query.order_by(asc(sort_column), asc(Job.id))
        
        # Apply cursor filtering if provided
        if pagination.cursor:
            cursor_data = CursorGenerator.parse_cursor(pagination.cursor)
            cursor_value = cursor_data.get('sort_value')
            cursor_id = cursor_data['id']
            
            # Apply cursor filter based on sort order
            if pagination.sort_order == 'desc':
                if cursor_value is not None:
                    base_query = base_query.filter(
                        or_(
                            sort_column < cursor_value,
                            and_(sort_column == cursor_value, Job.id < cursor_id)
                        )
                    )
                else:
                    base_query = base_query.filter(Job.id < cursor_id)
            else:
                if cursor_value is not None:
                    base_query = base_query.filter(
                        or_(
                            sort_column > cursor_value,
                            and_(sort_column == cursor_value, Job.id > cursor_id)
                        )
                    )
                else:
                    base_query = base_query.filter(Job.id > cursor_id)
        
        # Get total count if requested (expensive operation)
        total_count = None
        if pagination.include_total:
            total_count = base_query.count()
        
        # Fetch one extra item to determine if there's a next page
        items = base_query.limit(pagination.page_size + 1).all()
        
        # Determine pagination state
        has_next = len(items) > pagination.page_size
        if has_next:
            items = items[:-1]  # Remove the extra item
        
        has_previous = pagination.cursor is not None
        
        # Generate cursors
        next_cursor = None
        previous_cursor = None
        
        if has_next and items:
            last_item = items[-1]
            sort_value = getattr(last_item, pagination.sort_by)
            next_cursor = CursorGenerator.generate_cursor(
                last_item.id, sort_value, pagination.sort_by, pagination.sort_order
            )
        
        if has_previous and items:
            first_item = items[0]
            sort_value = getattr(first_item, pagination.sort_by)
            # For previous cursor, reverse the sort order
            reverse_order = 'asc' if pagination.sort_order == 'desc' else 'desc'
            previous_cursor = CursorGenerator.generate_cursor(
                first_item.id, sort_value, pagination.sort_by, reverse_order
            )
        
        # Create pagination metadata
        metadata = PaginationMetadata(
            page_size=pagination.page_size,
            total_count=total_count,
            has_next=has_next,
            has_previous=has_previous,
            next_cursor=next_cursor,
            previous_cursor=previous_cursor,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order
        )
        
        return {
            'items': items,
            'metadata': metadata
        }


class JobQueryFilters(BaseSchema):
    """Advanced filtering options for job queries."""
    
    status: Optional[str] = Field(
        None,
        max_length=20,
        description="Filter by job status"
    )
    model_used: Optional[str] = Field(
        None,
        max_length=50,
        description="Filter by Whisper model used"
    )
    created_after: Optional[datetime] = Field(
        None,
        description="Filter jobs created after this date"
    )
    created_before: Optional[datetime] = Field(
        None,
        description="Filter jobs created before this date"
    )
    completed_after: Optional[datetime] = Field(
        None,
        description="Filter jobs completed after this date"
    )
    completed_before: Optional[datetime] = Field(
        None,
        description="Filter jobs completed before this date"
    )
    min_file_size: Optional[int] = Field(
        None,
        ge=0,
        description="Minimum file size in bytes"
    )
    max_file_size: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum file size in bytes"
    )
    min_duration: Optional[int] = Field(
        None,
        ge=0,
        description="Minimum duration in seconds"
    )
    max_duration: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum duration in seconds"
    )
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate job status."""
        if v is None:
            return v
            
        v = sanitize_string(v)
        valid_statuses = ['pending', 'processing', 'completed', 'failed', 'cancelled']
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        return v
    
    @field_validator('model_used')
    @classmethod  
    def validate_model_used(cls, v: Optional[str]) -> Optional[str]:
        """Validate Whisper model name."""
        if v is None:
            return v
            
        v = sanitize_string(v)
        valid_models = ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3']
        if v not in valid_models:
            raise ValueError(f"Invalid model. Must be one of: {', '.join(valid_models)}")
        
        return v
    
    def apply_filters(self, query: Query) -> Query:
        """Apply filters to a SQLAlchemy query."""
        from api.models import Job  # Import here to avoid circular imports
        
        if self.status:
            query = query.filter(Job.status == self.status)
        
        if self.model_used:
            query = query.filter(Job.model_used == self.model_used)
        
        if self.created_after:
            query = query.filter(Job.created_at >= self.created_after)
        
        if self.created_before:
            query = query.filter(Job.created_at <= self.created_before)
        
        if self.completed_after:
            query = query.filter(Job.completed_at >= self.completed_after)
        
        if self.completed_before:
            query = query.filter(Job.completed_at <= self.completed_before)
        
        if self.min_file_size is not None:
            query = query.filter(Job.file_size >= self.min_file_size)
        
        if self.max_file_size is not None:
            query = query.filter(Job.file_size <= self.max_file_size)
        
        if self.min_duration is not None:
            query = query.filter(Job.duration >= self.min_duration)
        
        if self.max_duration is not None:
            query = query.filter(Job.duration <= self.max_duration)
        
        return query
