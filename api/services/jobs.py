from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import or_

from api.models import Job, JobStatusEnum, TranscriptMetadata
from api.orm_bootstrap import SessionLocal
from api.utils.db_lock import db_lock


def create_job(
    job_id: str,
    original_filename: str,
    saved_filename: str,
    model: str,
    created_at: datetime,
) -> Job:
    """Create a new Job record."""
    with db_lock:
        with SessionLocal() as db:
            job = Job(
                id=job_id,
                original_filename=original_filename,
                saved_filename=saved_filename,
                model=model,
                created_at=created_at,
                status=JobStatusEnum.QUEUED,
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            return job


def list_jobs(search: Optional[str] = None, status: Optional[str] = None) -> List[Job]:
    """Return jobs optionally filtered by search string and status."""
    with SessionLocal() as db:
        query = db.query(Job).outerjoin(
            TranscriptMetadata, Job.id == TranscriptMetadata.job_id
        )
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Job.original_filename.ilike(pattern),
                    Job.id.ilike(pattern),
                    TranscriptMetadata.keywords.ilike(pattern),
                )
            )

        if status:
            statuses = [s.strip() for s in status.split("|") if s.strip()]
            conditions = []
            for s in statuses:
                if s == "failed":
                    fail_statuses = [
                        status
                        for status in JobStatusEnum
                        if status.value.startswith("failed")
                    ]
                    conditions.append(Job.status.in_(fail_statuses))
                    continue
                try:
                    enum_val = JobStatusEnum(s)
                except ValueError:
                    continue
                conditions.append(Job.status == enum_val)
            if conditions:
                query = query.filter(or_(*conditions))

        return query.order_by(Job.created_at.desc()).all()


def get_job(job_id: str) -> Optional[Job]:
    """Fetch a job by id."""
    with SessionLocal() as db:
        return db.query(Job).filter_by(id=job_id).first()


def get_metadata(job_id: str) -> Optional[TranscriptMetadata]:
    """Return transcript metadata for a job if available."""
    with SessionLocal() as db:
        return db.query(TranscriptMetadata).filter_by(job_id=job_id).first()


def delete_job(job_id: str) -> Optional[Job]:
    """Delete a job and return the removed record."""
    with db_lock:
        with SessionLocal() as db:
            job = db.query(Job).filter_by(id=job_id).first()
            if not job:
                return None
            db.delete(job)
            db.commit()
            return job


def update_job_status(job_id: str, status: JobStatusEnum) -> Optional[Job]:
    """Update a job's status."""
    with db_lock:
        with SessionLocal() as db:
            job = db.query(Job).filter_by(id=job_id).first()
            if not job:
                return None
            job.status = status
            db.commit()
            db.refresh(job)
            return job


def update_analysis(
    job_id: str,
    summary: str,
    keywords: list[str] | str,
    language: str | None,
    sentiment: float | None,
) -> TranscriptMetadata:
    """Store analysis results in the metadata table."""
    with db_lock:
        with SessionLocal() as db:
            metadata = db.query(TranscriptMetadata).filter_by(job_id=job_id).first()
            if not metadata:
                metadata = TranscriptMetadata(
                    job_id=job_id,
                    tokens=0,
                    duration=0,
                    abstract="",
                    generated_at=datetime.utcnow(),
                )
                db.add(metadata)
            metadata.summary = summary
            kw_list = (
                [k.strip() for k in keywords.split(",") if k.strip()]
                if isinstance(keywords, str)
                else keywords
            )
            metadata.keywords = ", ".join(kw_list)
            metadata.language = language
            metadata.sentiment = sentiment
            db.commit()
            db.refresh(metadata)
            return metadata
