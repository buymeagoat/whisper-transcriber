from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# ─── Enum Class ─────────────────────────────────────────────────────────
class JobStatusEnum(PyEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    ENRICHING = "enriching"
    COMPLETED = "completed"
    FAILED = "failed"
    STALLED = "stalled"


# ─── Jobs Table ─────────────────────────────────────────────────────────
class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    original_filename = Column(String, nullable=False)
    saved_filename = Column(String, nullable=False)
    model = Column(String, nullable=False)
    status = Column(Enum(JobStatusEnum), nullable=False, default=JobStatusEnum.QUEUED)
    transcript_path = Column(String, nullable=True)
    log_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Job id={self.id} status={self.status.value}>"


# ─── MVP Metadata Table ─────────────────────────────────────────────────
class TranscriptMetadata(Base):
    __tablename__ = "metadata"

    job_id = Column(String, primary_key=True)
    tokens = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    abstract = Column(Text, nullable=False)
    sample_rate = Column(Integer, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Metadata job_id={self.job_id} tokens={self.tokens} duration={self.duration}>"
