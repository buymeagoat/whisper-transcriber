"""
Database ORM bootstrap for the Whisper Transcriber API.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from api.settings import settings
from api.utils.logger import get_system_logger

logger = get_system_logger("database")

# Database setup
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    poolclass=StaticPool if "sqlite" in settings.database_url else None,
    echo=settings.debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def validate_or_initialize_database():
    """Validate or initialize the database."""
    try:
        # Check if database file exists (for SQLite)
        if settings.database_url.startswith("sqlite"):
            db_path = settings.database_url.replace("sqlite:///", "")
            if not Path(db_path).exists():
                logger.info(f"Creating database file: {db_path}")
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("Database connection validated")
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables validated/created")
        
        return True
    
    except Exception as e:
        logger.error(f"Database validation failed: {e}")
        return False

def get_database_info():
    """Get database information."""
    try:
        with engine.connect() as conn:
            if "sqlite" in settings.database_url:
                result = conn.execute(text("SELECT sqlite_version()"))
                version = result.fetchone()[0]
                return {
                    "type": "SQLite",
                    "version": version,
                    "url": settings.database_url
                }
            else:
                return {
                    "type": "Unknown",
                    "version": "Unknown",
                    "url": settings.database_url
                }
    except Exception as e:
        return {
            "type": "Error",
            "version": str(e),
            "url": settings.database_url
        }
