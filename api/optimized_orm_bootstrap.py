"""
Optimized Database ORM Bootstrap - I005 Infrastructure Issue
Enhanced database bootstrap with optimized configuration
"""

import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from api.settings import settings
from api.optimized_database_config import create_optimized_database_configuration
from api.utils.logger import get_system_logger

logger = get_system_logger("database_optimized")

# Create optimized database configuration
db_config = create_optimized_database_configuration()

# Create optimized engine
try:
    optimized_engine = db_config.create_optimized_engine()
    logger.info("Using optimized database engine configuration")
except Exception as e:
    logger.error(f"Failed to create optimized engine, falling back to basic configuration: {e}")
    # Fallback to basic configuration
    optimized_engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
        echo=settings.debug
    )

# Create optimized session factory
OptimizedSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=optimized_engine)
Base = declarative_base()


def get_optimized_db() -> Session:
    """Get optimized database session."""
    db = OptimizedSessionLocal()
    try:
        yield db
    finally:
        db.close()


def validate_optimized_database():
    """Validate optimized database configuration and apply runtime optimizations."""
    try:
        # Validate configuration
        validation_results = db_config.validate_configuration()
        
        if not validation_results["configuration_valid"]:
            logger.error("Database configuration validation failed")
            for warning in validation_results["warnings"]:
                logger.warning(warning)
            return False
        
        # Log configuration status
        logger.info(f"Database type: {validation_results['database_type']}")
        
        for warning in validation_results["warnings"]:
            logger.warning(warning)
        
        for recommendation in validation_results["recommendations"]:
            logger.info(f"Recommendation: {recommendation}")
        
        # Apply runtime optimizations
        db_config.apply_runtime_optimizations(optimized_engine)
        
        # Test connection
        with optimized_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("Optimized database connection validated")
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=optimized_engine)
        logger.info("Database tables validated/created with optimized engine")
        
        return True
    
    except Exception as e:
        logger.error(f"Optimized database validation failed: {e}")
        return False


def get_optimized_database_info():
    """Get optimized database information."""
    try:
        validation_results = db_config.validate_configuration()
        
        with optimized_engine.connect() as conn:
            if "sqlite" in settings.database_url:
                version = conn.execute(text("SELECT sqlite_version()")).scalar()
                
                # Get performance settings
                performance_settings = validation_results.get("performance_settings", {})
                
                return {
                    "type": "SQLite (Optimized)",
                    "version": version,
                    "url": settings.database_url,
                    "optimizations": performance_settings,
                    "engine_config": "Optimized with WAL mode, increased cache, and performance tuning"
                }
            else:
                return {
                    "type": "PostgreSQL (Optimized)",
                    "version": "Unknown",
                    "url": settings.database_url,
                    "optimizations": validation_results.get("performance_settings", {}),
                    "engine_config": "Optimized with connection pooling and performance tuning"
                }
    except Exception as e:
        return {
            "type": "Error",
            "version": str(e),
            "url": settings.database_url,
            "optimizations": {},
            "engine_config": "Failed to determine configuration"
        }


def get_connection_pool_status() -> dict:
    """Get current connection pool status."""
    try:
        pool = optimized_engine.pool
        
        return {
            "pool_class": type(pool).__name__,
            "pool_size": getattr(pool, '_pool_size', getattr(pool, 'size', lambda: 'N/A')()),
            "checked_out": getattr(pool, 'checkedout', lambda: 'N/A')(),
            "checked_in": getattr(pool, 'checkedin', lambda: 'N/A')(),
            "overflow": getattr(pool, 'overflow', lambda: 'N/A')(),
            "invalid": getattr(pool, 'invalid', lambda: 'N/A')(),
        }
    except Exception as e:
        return {"error": str(e)}


def apply_database_optimizations():
    """Apply additional database optimizations at runtime."""
    try:
        logger.info("Applying database optimizations...")
        
        with optimized_engine.connect() as conn:
            if db_config.database_type == "sqlite":
                # SQLite-specific optimizations
                optimizations = [
                    "PRAGMA optimize",
                    "PRAGMA wal_checkpoint(TRUNCATE)",  # Checkpoint WAL file
                    "PRAGMA integrity_check",  # Quick integrity check
                ]
                
                for pragma in optimizations:
                    try:
                        result = conn.execute(text(pragma))
                        if pragma == "PRAGMA integrity_check":
                            integrity_result = result.scalar()
                            if integrity_result != "ok":
                                logger.warning(f"Database integrity check failed: {integrity_result}")
                            else:
                                logger.info("Database integrity check passed")
                    except Exception as e:
                        logger.warning(f"Failed to execute {pragma}: {e}")
                
                conn.commit()
                
            elif db_config.database_type == "postgresql":
                # PostgreSQL-specific optimizations
                conn.execute(text("ANALYZE"))
                conn.commit()
                logger.info("PostgreSQL ANALYZE completed")
        
        logger.info("Database optimizations applied successfully")
        
    except Exception as e:
        logger.error(f"Failed to apply database optimizations: {e}")


# Initialize optimized database on import
if __name__ != "__main__":
    try:
        if validate_optimized_database():
            apply_database_optimizations()
            logger.info("Optimized database bootstrap completed successfully")
        else:
            logger.warning("Optimized database validation failed, using basic configuration")
    except Exception as e:
        logger.error(f"Optimized database bootstrap failed: {e}")


# Export optimized components
__all__ = [
    'optimized_engine',
    'OptimizedSessionLocal', 
    'Base',
    'get_optimized_db',
    'validate_optimized_database',
    'get_optimized_database_info',
    'get_connection_pool_status',
    'apply_database_optimizations',
    'db_config'
]