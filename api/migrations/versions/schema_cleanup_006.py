"""Schema cleanup: Remove redundant lang field and add performance indexes

Revision ID: schema_cleanup_006
Revises: b8b3752f3e16
Create Date: 2025-10-11
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = "schema_cleanup_006"
down_revision: Union[str, None] = "b8b3752f3e16"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Schema cleanup improvements."""
    
    # 1. Remove redundant 'lang' field from metadata table
    # First migrate any existing data from 'lang' to 'language' if needed
    op.execute("""
        UPDATE metadata 
        SET language = lang 
        WHERE language IS NULL AND lang IS NOT NULL
    """)
    
    # Drop the redundant lang column
    op.drop_column("metadata", "lang")
    
    # 2. Add performance indexes for common queries
    # Index on jobs status for filtering
    op.create_index("idx_jobs_status", "jobs", ["status"])
    
    # Index on jobs created_at for sorting/filtering
    op.create_index("idx_jobs_created_at", "jobs", ["created_at"])
    
    # Composite index for status + created_at queries
    op.create_index("idx_jobs_status_created", "jobs", ["status", "created_at"])
    
    # Index on jobs model for filtering
    op.create_index("idx_jobs_model", "jobs", ["model"])
    
    # 3. Add index on metadata job_id for faster joins (if not already primary key constraint)
    # This helps with metadata lookups by job_id
    op.create_index("idx_metadata_job_id", "metadata", ["job_id"])
    
    # 4. Improve user table indexes
    # Index on username for faster login lookups (if not already unique constraint)
    op.create_index("idx_users_username", "users", ["username"])
    
    # Index on role for admin queries
    op.create_index("idx_users_role", "users", ["role"])
    
    # 5. Add constraints for data integrity
    # Ensure created_at and updated_at are not null
    op.alter_column("jobs", "created_at", nullable=False)
    op.alter_column("jobs", "updated_at", nullable=False)
    
    # Ensure metadata required fields are not null
    op.alter_column("metadata", "tokens", nullable=False)
    op.alter_column("metadata", "duration", nullable=False) 
    op.alter_column("metadata", "abstract", nullable=False)
    op.alter_column("metadata", "generated_at", nullable=False)
    
    # 6. Optimize AuditLog indexes (remove potential duplicates, keep efficient ones)
    # The existing indexes in the model are already well-designed, no changes needed


def downgrade() -> None:
    """Reverse schema cleanup changes."""
    
    # 6. Remove added indexes (in reverse order)
    op.drop_index("idx_users_role", "users")
    op.drop_index("idx_users_username", "users")
    op.drop_index("idx_metadata_job_id", "metadata")
    op.drop_index("idx_jobs_model", "jobs")
    op.drop_index("idx_jobs_status_created", "jobs")
    op.drop_index("idx_jobs_created_at", "jobs") 
    op.drop_index("idx_jobs_status", "jobs")
    
    # 5. Revert constraint changes
    op.alter_column("metadata", "generated_at", nullable=True)
    op.alter_column("metadata", "abstract", nullable=True)
    op.alter_column("metadata", "duration", nullable=True)
    op.alter_column("metadata", "tokens", nullable=True)
    op.alter_column("jobs", "updated_at", nullable=True)
    op.alter_column("jobs", "created_at", nullable=True)
    
    # 1. Restore the redundant 'lang' field
    op.add_column("metadata", sa.Column("lang", sa.String(), nullable=True))
    
    # Migrate data back from 'language' to 'lang' if needed
    op.execute("""
        UPDATE metadata 
        SET lang = language 
        WHERE lang IS NULL AND language IS NOT NULL
    """)
