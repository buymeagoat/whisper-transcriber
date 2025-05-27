# api/models.py

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Job(Base):
    """
    Table: jobs
    Tracks each transcription request and its output status.
    - transcript_path: now refers to transcript.md under transcripts/{job_id}/
    """
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    original_filename = Column(String, nullable=False)
    saved_filename = Column(String, nullable=False)
    model = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    status = Column(String, nullable=False)
    transcript_path = Column(String)  # Path to transcript.md
    error_message = Column(Text)

class Metadata(Base):
    """
    Table: metadata
    Per-job enrichment: abstract, keywords, duration, vector ID, etc.
    """
    __tablename__ = "metadata"
    job_id = Column(String, ForeignKey("jobs.id"), primary_key=True)
    lang = Column(String)
    tokens = Column(Integer)
    duration = Column(Float)
    abstract = Column(Text)
    keywords = Column(Text)
    vector_id = Column(String)

class Heartbeat(Base):
    """
    Table: heartbeats
    Tracks active worker pings to detect stall/dead jobs.
    """
    __tablename__ = "heartbeats"
    job_id = Column(String, ForeignKey("jobs.id"), primary_key=True)
    last_seen = Column(DateTime, nullable=False)

class User(Base):
    """
    Table: users
    Placeholder for future login/auth integration.
    """
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    name = Column(String)
    role = Column(String)
    created_at = Column(DateTime)
