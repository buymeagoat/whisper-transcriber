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

# Import all models to ensure they're registered with Base.metadata
# This must happen after Base is defined but before create_all is called
try:
    import api.models  # noqa: F401
    logger.debug("Models imported successfully during bootstrap")
except Exception as e:
    logger.warning(f"Failed to import api.models during bootstrap: {e}")

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
        
            # Run Alembic migrations if AUTO_MIGRATE is enabled
            auto_migrate = getattr(settings, 'auto_migrate', False) or os.getenv("AUTO_MIGRATE", "false").lower() in ("true", "1", "yes")
            if auto_migrate:
                try:
                    from alembic.config import Config
                    from alembic import command
                    
                    # Get the directory containing this file to find alembic.ini
                    current_dir = Path(__file__).parent.parent  # Go up from api/ to root
                    alembic_ini_path = current_dir / "alembic.ini"
                    
                    if alembic_ini_path.exists():
                        alembic_cfg = Config(str(alembic_ini_path))
                        command.upgrade(alembic_cfg, "head")
                        logger.info("Alembic migrations applied successfully")
                    else:
                        logger.warning(f"Alembic config not found at {alembic_ini_path}, skipping migrations")
                except Exception as e:
                    logger.warning(f"Failed to run Alembic migrations: {e}")
                    logger.info("Falling back to create_all for table creation")

            # Create tables if they don't exist (fallback or when migrations disabled)
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
