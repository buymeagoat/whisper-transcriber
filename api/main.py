import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from api.utils.logger import get_system_logger
from api.exceptions import ConfigurationError, InitError

system_log = get_system_logger()

try:
    from api.settings import settings
    from api.config_validator import validate_config
    from api.paths import storage, UPLOAD_DIR, TRANSCRIPTS_DIR
    import api.app_state as app_state
    from api.app_state import (
        handle_whisper,
        LOCAL_TZ,
        backend_log,
        start_cleanup_thread,
        stop_cleanup_thread,
        check_celery_connection,
    )
    from api.services.job_queue import ThreadJobQueue


    from api.middlewares.api_cache import ApiCacheMiddleware, CacheConfig

    
    # Enhanced caching system for T025 Phase 2
    from api.services.redis_cache import (
        initialize_cache_service, 
        cleanup_cache_service, 
        CacheConfiguration
    )
    from api.middlewares.enhanced_cache import EnhancedApiCacheMiddleware
    
    # Audit logging system for T026 Security Hardening
    from api.audit.security_audit_logger import initialize_audit_logging
    
    # T026 Security Hardening - Secure logging utilities
    from api.utils.log_sanitization import safe_log_format, sanitize_for_log
    
    # T026 Security Hardening - Comprehensive security middleware
    from api.security.middleware import create_security_middleware_stack
    
    # T027 API Key Management - API key authentication middleware
    from api.middlewares.api_key_auth import APIKeyAuthenticationMiddleware
    
    # Enhanced database optimization for T025 Phase 3 - TEMPORARILY DISABLED FOR DEBUGGING
    # from api.services.database_optimization_integration import (
    #     get_optimization_service,
    #     cleanup_optimization_service,
    #     database_optimization_lifespan
    # )
    
    # Enhanced WebSocket service for T025 Phase 4
    from api.services.enhanced_websocket_service import (
        get_websocket_service,
        cleanup_websocket_service,
        websocket_service_lifespan
    )
    from api.services.websocket_job_integration import (
        get_job_notifier,
        setup_job_event_listeners
    )
    
    # Chunked upload service for T025 Phase 5
    from api.services.chunked_upload_service import (
        chunked_upload_service,
        ChunkedUploadService
    )

    # Import backup service management if available
    try:
        # Backup service temporarily disabled during consolidation  
        # from app.backup_api import (
        #     initialize_backup_service,
        #     start_backup_service_if_configured,
        #     shutdown_backup_service
        # )
        # BACKUP_SERVICE_AVAILABLE = True
        BACKUP_SERVICE_AVAILABLE = False
        # Define dummy functions for disabled backup service
        def initialize_backup_service():
            return False
        def start_backup_service_if_configured():
            return False  
        def shutdown_backup_service():
            pass
        system_log.info("Backup service disabled during architecture consolidation")
    except ImportError:
        system_log.warning("Backup service not available - backup features disabled")
        BACKUP_SERVICE_AVAILABLE = False

    validate_config()
except (ConfigurationError, InitError) as exc:  # pragma: no cover - startup fail
    system_log.critical(str(exc))
    raise SystemExit(1)

from api.orm_bootstrap import SessionLocal, validate_or_initialize_database, get_db
from api.models import Job
from api.models import JobStatusEnum
from api.services.users import ensure_default_admin
from api.utils.model_validation import validate_models_dir
from api.router_setup import register_routes
from api.middlewares.access_log import AccessLogMiddleware
from api.utils.db_lock import db_lock
from functools import partial


def log_startup_settings() -> None:
    """Log key configuration settings."""
    # T026 Security: Fixed log injection vulnerability - use safe formatting
    system_log.info(safe_log_format(
        "db_url={}, job_queue_backend={}, storage_backend={}, log_level={}",
        sanitize_for_log(settings.db_url),
        sanitize_for_log(settings.job_queue_backend),
        sanitize_for_log(settings.storage_backend),
        sanitize_for_log(settings.log_level)
    ))


# ─── Paths ───
ROOT = Path(__file__).parent

# ─── ENV SAFETY CHECK ───
# Read API host from environment with a default for local development.
API_HOST = settings.vite_api_host
if "VITE_API_HOST" not in os.environ:
    system_log.warning("VITE_API_HOST not set, defaulting to http://localhost:8001")


# ─── Lifespan Hook ───
@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan events."""
    system_log.info("Starting app initialization...")
    
    # Initialize audit logging system for T026 Security Hardening
    try:
        audit_logger = initialize_audit_logging(enable_integrity=True)
        system_log.info("Security audit logging system initialized successfully")
    except Exception as e:
        system_log.warning(f"Failed to initialize audit logging: {e}")
    
    # Database initialization
    validate_or_initialize_database()
    ensure_default_admin()
    
    # Model validation
    validate_models_dir()

    # Initialize enhanced cache service for T025 Phase 2
    try:
        cache_config = CacheConfiguration(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            default_ttl=int(os.getenv("CACHE_DEFAULT_TTL", "300")),
            max_memory_mb=int(os.getenv("CACHE_MAX_MEMORY_MB", "100")),
            enable_smart_invalidation=True,
            cache_warming=True,
            track_hit_ratio=True,
            log_cache_operations=settings.log_level == "DEBUG"
        )
        await initialize_cache_service(cache_config)
        system_log.info("Enhanced Redis cache service initialized successfully")
    except Exception as e:
        system_log.warning(f"Failed to initialize cache service: {e}")

    # Initialize job queue
    try:
        from api.app_state import initialize_job_queue
        initialize_job_queue()
        system_log.info("Job queue initialized successfully")
    except Exception as e:
        system_log.warning(f"Failed to initialize job queue: {e}")
        # Set a fallback job queue directly
        app_state.app_state["job_queue"] = ThreadJobQueue()

    # Initialize enhanced database optimization for T025 Phase 3 - TEMPORARILY DISABLED
    try:
        # optimization_service = await get_optimization_service()
        system_log.info("Database optimization service temporarily disabled for debugging")
    except Exception as e:
        system_log.warning(f"Failed to initialize database optimization service: {e}")

    # Initialize database performance monitoring for I005
    try:
        from api.database_performance_monitor import initialize_monitoring, log_alert_handler, metrics_alert_handler
        
        monitor = initialize_monitoring(start_collection=True, collection_interval=30)
        
        # Register alert handlers
        monitor.register_alert_handler(log_alert_handler)
        monitor.register_alert_handler(metrics_alert_handler)
        
        system_log.info("Database performance monitoring initialized successfully")
    except Exception as e:
        system_log.warning(f"Failed to initialize database performance monitoring: {e}")

    # Initialize enhanced WebSocket service for T025 Phase 4
    websocket_service = None
    try:
        websocket_service = await get_websocket_service()
        job_notifier = await get_job_notifier()
        setup_job_event_listeners()
        system_log.info("Enhanced WebSocket service initialized successfully")
    except Exception as e:
        system_log.warning(f"Failed to initialize WebSocket service: {e}")

    # Initialize chunked upload service for T025 Phase 5
    try:
        # Initialize chunked upload service with WebSocket integration
        chunked_upload_service.progress_tracker.websocket_service = websocket_service
        system_log.info(f"Chunked upload service initialized successfully (WebSocket: {'enabled' if websocket_service else 'disabled'})")
    except Exception as e:
        system_log.warning(f"Failed to initialize chunked upload service: {e}")

    # Start background threads
    start_cleanup_thread()
    
    # Initialize backup service if available
    if BACKUP_SERVICE_AVAILABLE:
        try:
            if initialize_backup_service():
                system_log.info("Backup service initialized successfully")
                # Optionally start backup service with scheduling
                if start_backup_service_if_configured():
                    system_log.info("Backup service started with scheduling")
            else:
                system_log.warning("Backup service initialization failed")
        except Exception as e:
            system_log.error(f"Error initializing backup service: {e}")

    # Rehydrate incomplete jobs at startup
    rehydrate_incomplete_jobs()
    
    system_log.info("App initialization complete.")

    yield  # app runs here

    system_log.info("Shutting down app...")
    
    # Cleanup enhanced cache service
    try:
        await cleanup_cache_service()
        system_log.info("Cache service shutdown completed")
    except Exception as e:
        system_log.error(f"Error shutting down cache service: {e}")
    
    # Cleanup enhanced database optimization service - TEMPORARILY DISABLED
    try:
        # await cleanup_optimization_service()
        system_log.info("Database optimization service cleanup skipped (disabled)")
    except Exception as e:
        system_log.error(f"Error shutting down database optimization service: {e}")
    
    # Cleanup enhanced WebSocket service
    try:
        await cleanup_websocket_service()
        system_log.info("WebSocket service shutdown completed")
    except Exception as e:
        system_log.error(f"Error shutting down WebSocket service: {e}")
    
    # Cleanup chunked upload service
    try:
        chunked_upload_service.cleanup()
        system_log.info("Chunked upload service shutdown completed")
    except Exception as e:
        system_log.error(f"Error shutting down chunked upload service: {e}")

    # Cleanup database performance monitoring
    try:
        from api.database_performance_monitor import cleanup_monitoring
        cleanup_monitoring()
        system_log.info("Database performance monitoring shutdown completed")
    except Exception as e:
        system_log.error(f"Error shutting down database performance monitoring: {e}")
    
    # Shutdown backup service gracefully
    if BACKUP_SERVICE_AVAILABLE:
        try:
            shutdown_backup_service()
            system_log.info("Backup service shutdown completed")
        except Exception as e:
            system_log.error(f"Error shutting down backup service: {e}")
    
    # Stop background threads
    stop_cleanup_thread()


log_startup_settings()
system_log.info("FastAPI app initialization starting.")

# ─── App Setup ───
app = FastAPI(lifespan=lifespan)

# ─── Security Hardening Middleware Stack (T027) ───
# Apply comprehensive security middleware stack
security_middleware_stack = create_security_middleware_stack()
app = security_middleware_stack(app)

# ─── API Key Authentication Middleware (T027) ───
app.add_middleware(APIKeyAuthenticationMiddleware)

# ─── Middleware ───
# Enhanced API Response Caching with Redis (T025 Phase 2)
enhanced_cache_config = CacheConfiguration(
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    default_ttl=300,  # 5 minutes
    job_status_ttl=60,  # 1 minute for frequently changing job status
    job_list_ttl=120,  # 2 minutes for job lists
    user_data_ttl=600,  # 10 minutes for user data
    static_data_ttl=3600,  # 1 hour for health/version endpoints
    max_memory_mb=100,
    compression_threshold=1024,
    enable_smart_invalidation=True,
    cache_warming=True,
    track_hit_ratio=True,
    log_cache_operations=settings.log_level == "DEBUG"
)
app.add_middleware(EnhancedApiCacheMiddleware, config=enhanced_cache_config)

# Enhanced Security Headers with environment-specific configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AccessLogMiddleware)


# ─── Static File Routes ───
@app.get("/health")
def health_check():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        system_log.error(f"Health check failed: {exc}")
        return JSONResponse(status_code=500, content={"status": "db_error"})


@app.get("/version")
def version() -> dict:
    """Return the application version from pyproject.toml."""
    try:
        pyproject = ROOT.parent / "pyproject.toml"
        try:
            import tomllib
        except ImportError:
            # Fallback for Python < 3.11
            import tomli as tomllib
        
        data = tomllib.loads(pyproject.read_text())
        version = data.get("project", {}).get("version", "unknown")
        return {"version": version}
    except Exception as e:
        return {"version": "error", "details": str(e)}


def rehydrate_incomplete_jobs():
    with SessionLocal() as db:
        jobs = (
            db.query(Job)
            .filter(
                Job.status.in_(
                    [
                        JobStatusEnum.QUEUED,
                        JobStatusEnum.PROCESSING,
                        JobStatusEnum.ENRICHING,
                    ]
                )
            )
            .all()
        )
        for job in jobs:
            backend_log.info(f"Rehydrating job {job.id} with model '{job.model}'")
            try:
                upload_path = storage.get_upload_path(job.saved_filename)
                job_dir = storage.get_transcript_dir(job.id)
                app_state.app_state["job_queue"].enqueue(
                    partial(
                        handle_whisper,
                        str(upload_path),
                        model=job.model,
                        job_id=job.id
                    )
                )
            except Exception as e:
                backend_log.error(f"Failed to rehydrate job {job.id}: {e}")


# ─── Register Routers ─────────────────────────────────────
register_routes(app)

# ─── Run Application ──────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )