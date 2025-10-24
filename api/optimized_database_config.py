"""
Optimized Database Configuration - I005 Infrastructure Issue
Enhanced database configuration for both SQLite optimization and PostgreSQL preparation
"""

import os
from typing import Dict, Any, Optional, Union
from urllib.parse import urlparse, parse_qs
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool, QueuePool, NullPool
from sqlalchemy.orm import sessionmaker

from api.settings import settings
from api.utils.logger import get_system_logger

logger = get_system_logger("db_config")


class DatabaseConfiguration:
    """Advanced database configuration management"""
    
    def __init__(self):
        self.database_type = self._detect_database_type(settings.database_url)
        self.optimized_settings = {}
        
    def _detect_database_type(self, database_url: str) -> str:
        """Detect database type from URL"""
        if database_url.startswith("sqlite"):
            return "sqlite"
        elif database_url.startswith("postgresql"):
            return "postgresql"
        elif database_url.startswith("mysql"):
            return "mysql"
        else:
            return "unknown"
    
    def get_optimized_sqlite_url(self) -> str:
        """Get optimized SQLite connection URL with performance parameters"""
        base_url = settings.database_url
        
        # Parse existing URL
        if "?" in base_url:
            base_url, existing_params = base_url.split("?", 1)
        else:
            existing_params = ""
        
        # Optimized SQLite parameters for better performance
        optimized_params = {
            # Enable WAL mode for better concurrent read performance
            "mode": "wal",
            
            # Set cache size to 64MB (negative value means KB, positive means pages)
            "cache": "shared",
            
            # Connection timeout
            "timeout": "20000",  # 20 seconds
            
            # Enable foreign keys
            "foreign_keys": "1",
            
            # Synchronous mode for balance of performance and durability
            "synchronous": "NORMAL",
            
            # Journal mode - WAL is best for concurrent access
            "journal_mode": "WAL",
            
            # Page size optimization
            "page_size": "4096",
            
            # Temp store in memory for better performance
            "temp_store": "MEMORY",
            
            # Optimize busy timeout
            "busy_timeout": "30000"  # 30 seconds
        }
        
        # Combine with existing parameters
        if existing_params:
            existing_dict = dict(param.split("=") for param in existing_params.split("&") if "=" in param)
            # Existing params take precedence
            optimized_params.update(existing_dict)
        
        # Build optimized URL
        param_string = "&".join(f"{k}={v}" for k, v in optimized_params.items())
        optimized_url = f"{base_url}?{param_string}"
        
        logger.info(f"Optimized SQLite URL: {optimized_url}")
        return optimized_url
    
    def get_optimized_postgresql_url(self) -> str:
        """Get optimized PostgreSQL connection URL"""
        # This is for future use when migrating to PostgreSQL
        base_url = settings.database_url
        
        if not base_url.startswith("postgresql"):
            # Convert SQLite URL to PostgreSQL template
            return "postgresql://user:password@localhost:5432/whisper_transcriber"
        
        return base_url
    
    def get_optimized_engine_config(self) -> Dict[str, Any]:
        """Get optimized SQLAlchemy engine configuration"""
        if self.database_type == "sqlite":
            return self._get_sqlite_engine_config()
        elif self.database_type == "postgresql":
            return self._get_postgresql_engine_config()
        else:
            return self._get_default_engine_config()
    
    def _get_sqlite_engine_config(self) -> Dict[str, Any]:
        """Get SQLite-specific engine configuration"""
        config = {
            "url": self.get_optimized_sqlite_url(),
            "echo": settings.debug,
            "echo_pool": settings.debug,
            
            # SQLite connection arguments
            "connect_args": {
                "check_same_thread": False,  # Allow multi-threading
                "timeout": 30.0,  # Connection timeout
                # Additional pragma settings applied per connection
                "isolation_level": None,  # Use autocommit mode for better control
            },
            
            # Connection pooling - StaticPool for SQLite
            "poolclass": StaticPool,
            "pool_pre_ping": True,  # Verify connections before use
            "pool_recycle": 3600,   # Recycle connections every hour
            
            # Engine options
            "future": True,  # Use SQLAlchemy 2.0 style
            "query_cache_size": 1200,  # Cache compiled SQL statements
        }
        
        # Add event listeners for SQLite optimization
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragma settings for optimal performance"""
            cursor = dbapi_connection.cursor()
            
            # Performance optimizations
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-65536")  # 64MB cache
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory mapping
            cursor.execute("PRAGMA optimize")
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys=ON")
            
            # Set busy timeout
            cursor.execute("PRAGMA busy_timeout=30000")
            
            # Checkpoint WAL periodically
            cursor.execute("PRAGMA wal_autocheckpoint=1000")
            
            cursor.close()
            
            logger.debug("SQLite pragma settings applied for connection")
        
        return config
    
    def _get_postgresql_engine_config(self) -> Dict[str, Any]:
        """Get PostgreSQL-specific engine configuration"""
        config = {
            "url": self.get_optimized_postgresql_url(),
            "echo": settings.debug,
            "echo_pool": settings.debug,
            
            # PostgreSQL connection arguments
            "connect_args": {
                "connect_timeout": 30,
                "command_timeout": 60,
                "server_settings": {
                    "application_name": "whisper_transcriber",
                    "search_path": "public",
                }
            },
            
            # Connection pooling - QueuePool for PostgreSQL
            "poolclass": QueuePool,
            "pool_size": getattr(settings, 'DB_POOL_SIZE', 20),
            "max_overflow": getattr(settings, 'DB_MAX_OVERFLOW', 40),
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "pool_timeout": 30,
            
            # Engine options
            "future": True,
            "query_cache_size": 1200,
            
            # PostgreSQL specific options
            "isolation_level": "READ COMMITTED",
            "client_encoding": "utf8",
        }
        
        return config
    
    def _get_default_engine_config(self) -> Dict[str, Any]:
        """Get default engine configuration"""
        return {
            "url": settings.database_url,
            "echo": settings.debug,
            "poolclass": NullPool,  # No pooling for unknown databases
            "pool_pre_ping": True,
        }
    
    def create_optimized_engine(self) -> Engine:
        """Create optimized database engine"""
        config = self.get_optimized_engine_config()
        
        # Extract URL and other config
        url = config.pop("url")
        
        logger.info(f"Creating optimized {self.database_type} engine")
        
        engine = create_engine(url, **config)
        
        # Apply additional optimizations
        self._apply_engine_optimizations(engine)
        
        return engine
    
    def _apply_engine_optimizations(self, engine: Engine):
        """Apply additional engine-level optimizations"""
        
        # Connection pool monitoring
        @event.listens_for(engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            logger.debug(f"New {self.database_type} connection established")
            
        @event.listens_for(engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            logger.debug(f"Connection checked out from pool")
            
        @event.listens_for(engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            logger.debug(f"Connection checked in to pool")
        
        # Query performance monitoring (already handled by performance monitor)
        logger.info(f"Applied engine optimizations for {self.database_type}")
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current database configuration"""
        validation_results = {
            "database_type": self.database_type,
            "configuration_valid": True,
            "warnings": [],
            "recommendations": [],
            "performance_settings": {}
        }
        
        try:
            # Create test engine to validate configuration
            test_engine = self.create_optimized_engine()
            
            # Test connection
            with test_engine.connect() as conn:
                if self.database_type == "sqlite":
                    # Check SQLite settings
                    result = conn.execute(text("PRAGMA journal_mode")).scalar()
                    validation_results["performance_settings"]["journal_mode"] = result
                    
                    if result != "wal":
                        validation_results["warnings"].append("WAL mode not enabled - may impact concurrent performance")
                        validation_results["recommendations"].append("Enable WAL mode: PRAGMA journal_mode=WAL")
                    
                    cache_size = conn.execute(text("PRAGMA cache_size")).scalar()
                    validation_results["performance_settings"]["cache_size"] = cache_size
                    
                    if abs(cache_size) < 10000:
                        validation_results["warnings"].append("Cache size may be too small for optimal performance")
                        validation_results["recommendations"].append("Increase cache size to at least 64MB")
                    
                    synchronous = conn.execute(text("PRAGMA synchronous")).scalar()
                    validation_results["performance_settings"]["synchronous"] = synchronous
                    
                    foreign_keys = conn.execute(text("PRAGMA foreign_keys")).scalar()
                    validation_results["performance_settings"]["foreign_keys"] = bool(foreign_keys)
                    
                    if not foreign_keys:
                        validation_results["warnings"].append("Foreign keys not enabled")
                        validation_results["recommendations"].append("Enable foreign keys for data integrity")
                
                elif self.database_type == "postgresql":
                    # Check PostgreSQL settings
                    version = conn.execute(text("SELECT version()")).scalar()
                    validation_results["performance_settings"]["version"] = version
                    
                    # Check important PostgreSQL settings
                    settings_to_check = [
                        "max_connections",
                        "shared_buffers",
                        "effective_cache_size",
                        "work_mem"
                    ]
                    
                    for setting in settings_to_check:
                        try:
                            value = conn.execute(text(f"SHOW {setting}")).scalar()
                            validation_results["performance_settings"][setting] = value
                        except Exception as e:
                            logger.warning(f"Could not check {setting}: {e}")
            
            test_engine.dispose()
            
        except Exception as e:
            validation_results["configuration_valid"] = False
            validation_results["warnings"].append(f"Configuration validation failed: {str(e)}")
            logger.error(f"Database configuration validation failed: {e}")
        
        return validation_results
    
    def generate_postgresql_migration_config(self) -> Dict[str, Any]:
        """Generate PostgreSQL configuration for migration"""
        return {
            "connection_url": "postgresql://whisper_user:secure_password@localhost:5432/whisper_transcriber",
            "recommended_settings": {
                "max_connections": 100,
                "shared_buffers": "256MB",
                "effective_cache_size": "1GB",
                "work_mem": "4MB",
                "maintenance_work_mem": "64MB",
                "checkpoint_completion_target": 0.9,
                "wal_buffers": "16MB",
                "default_statistics_target": 100,
                "random_page_cost": 1.1,
                "effective_io_concurrency": 200,
                "min_wal_size": "1GB",
                "max_wal_size": "4GB",
            },
            "connection_pooling": {
                "pool_size": 20,
                "max_overflow": 40,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "pool_pre_ping": True
            },
            "performance_features": {
                "enable_indexing": True,
                "enable_full_text_search": True,
                "enable_json_storage": True,
                "enable_partitioning": True,
                "enable_read_replicas": True
            }
        }
    
    def apply_runtime_optimizations(self, engine: Engine):
        """Apply runtime database optimizations"""
        try:
            with engine.connect() as conn:
                if self.database_type == "sqlite":
                    # SQLite runtime optimizations
                    conn.execute(text("PRAGMA optimize"))
                    conn.commit()
                    logger.info("Applied SQLite runtime optimizations")
                
                elif self.database_type == "postgresql":
                    # PostgreSQL runtime optimizations
                    conn.execute(text("ANALYZE"))
                    conn.commit()
                    logger.info("Applied PostgreSQL runtime optimizations")
                    
        except Exception as e:
            logger.error(f"Failed to apply runtime optimizations: {e}")


def create_optimized_database_configuration() -> DatabaseConfiguration:
    """Create and return optimized database configuration"""
    config = DatabaseConfiguration()
    
    logger.info(f"Created optimized configuration for {config.database_type} database")
    
    return config


def get_production_recommendations() -> Dict[str, Any]:
    """Get production deployment recommendations"""
    return {
        "sqlite_limitations": {
            "concurrent_users": "5-10 maximum before performance degrades",
            "write_throughput": "Single writer limitation causes bottlenecks",
            "scaling": "Cannot scale horizontally",
            "backup": "Requires application downtime for consistent backups",
            "monitoring": "Limited performance monitoring capabilities"
        },
        "postgresql_benefits": {
            "concurrent_users": "100+ users with proper connection pooling",
            "write_throughput": "True concurrent writes with MVCC",
            "scaling": "Horizontal scaling with read replicas",
            "backup": "Zero-downtime backups with WAL archiving",
            "monitoring": "Comprehensive performance monitoring tools"
        },
        "migration_priority": "HIGH",
        "migration_timeline": "3-4 weeks for complete migration",
        "immediate_sqlite_improvements": [
            "Enable WAL mode for better concurrent reads",
            "Increase cache size to 64MB",
            "Implement connection timeout handling",
            "Add comprehensive performance monitoring",
            "Optimize query patterns to reduce N+1 queries"
        ]
    }


# Export optimized configuration instance
optimized_db_config = create_optimized_database_configuration()