from pathlib import Path
import logging

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response as StarletteResponse

from api.routes import jobs, admin, logs, metrics, auth, users, audit, cache
from api.routes import progress, audio, tts, user_settings, enhanced_cache
from api.routes import websockets, admin_websocket, admin_database_optimization
from api.routes import chunked_uploads, upload_websockets, admin_chunked_uploads
from api.routes import admin_security  # T026 Security Hardening admin routes
from api.routes import api_keys, admin_api_keys  # T027 API Key Management routes
from api.routes import batch  # T027 Batch Processing routes
from api.routes import pwa  # T027 PWA Enhancement routes
from api.routes import admin_system_performance  # T032 System Performance Dashboard routes
from api.routes import admin_system_resources  # T013 System Resource Usage Dashboard routes
from api.routes import transcript_management  # T033 Advanced Transcript Management routes
from api.routes import export_system  # T034 Multi-Format Export System routes
from api.routes import audio_processing  # T035 Audio Processing Pipeline routes
from api.routes import search  # T021 Transcript Search functionality
from api.routes import export  # T022 Multi-Format Export System
from api.routes import batch_upload  # T020 Batch Upload capabilities
from api.paths import storage, UPLOAD_DIR, TRANSCRIPTS_DIR
from api.app_state import backend_log

# Import backup API router
try:
    from api.routes.backup import backup_router
    BACKUP_API_AVAILABLE = True
except ImportError as e:
    backend_log.warning(f"Backup API not available: {e}")
    BACKUP_API_AVAILABLE = False


class CacheBustingStaticFiles(StaticFiles):
    """Custom StaticFiles that adds cache-busting headers for development"""
    
    def is_not_modified(self, response_headers, request_headers):
        # Always serve fresh files, bypassing cache
        return False
    
    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        if hasattr(response, 'headers'):
            # Add cache-busting headers
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


def register_routes(app: FastAPI) -> None:
    """Attach all API routers and static paths."""
    app.include_router(jobs.router)
    app.include_router(admin.router)
    app.include_router(logs.router)
    app.include_router(progress.router)
    app.include_router(metrics.router)
    app.include_router(auth.router)
    app.include_router(auth.api_router)  # Add API-prefixed auth routes
    app.include_router(auth.direct_api_router)  # Add direct API routes for /api/register
    app.include_router(auth.root_router)  # Add root-level auth routes
    app.include_router(users.router)
    app.include_router(audit.router, prefix="/admin", tags=["audit"])
    app.include_router(cache.router, prefix="/admin", tags=["cache"])
    
    # Enhanced cache management routes for T025 Phase 2
    app.include_router(enhanced_cache.router, tags=["enhanced_cache", "admin"])
    
    # Enhanced WebSocket routes for T025 Phase 4
    app.include_router(websockets.router, tags=["websockets", "real-time"])
    app.include_router(admin_websocket.router, tags=["admin", "websockets"])
    app.include_router(admin_database_optimization.router, tags=["admin", "database"])
    
    # Chunked upload routes for T025 Phase 5
    app.include_router(chunked_uploads.router, tags=["chunked-uploads", "file-upload"])
    app.include_router(upload_websockets.router, tags=["upload-websockets", "real-time"])
    app.include_router(admin_chunked_uploads.router, tags=["admin", "chunked-uploads"])
    
    # T026 Security Hardening admin routes
    app.include_router(admin_security.router, prefix="/admin", tags=["admin", "security"])
    
    # T027 API Key Management routes
    app.include_router(api_keys.router, tags=["api-keys"])
    app.include_router(admin_api_keys.router, tags=["admin", "api-keys"])
    
    # T027 Batch Processing routes
    app.include_router(batch.router, tags=["batch"])
    
    # T027 PWA Enhancement routes
    app.include_router(pwa.router, tags=["pwa"])
    
    # T032 System Performance Dashboard routes
    app.include_router(admin_system_performance.router, tags=["admin", "system-performance"])
    
    # T013 System Resource Usage Dashboard routes
    app.include_router(admin_system_resources.resource_router, tags=["admin", "system-resources"])
    
    # T033 Advanced Transcript Management routes
    app.include_router(transcript_management.router, tags=["transcript-management", "transcripts"])
    
    # T034 Multi-Format Export System routes
    app.include_router(export_system.router, tags=["export-system", "exports"])
    
    # T035 Audio Processing Pipeline routes
    app.include_router(audio_processing.router, tags=["audio-processing", "enhancement"])
    
    # T021 Transcript Search functionality routes  
    app.include_router(search.router, tags=["search", "transcripts"])
    
    # T022 Multi-Format Export routes
    app.include_router(export.router, tags=["export", "formats"])
    
    # T020 Batch Upload capabilities routes
    app.include_router(batch_upload.router, tags=["batch-upload", "uploads"])
    
    # Include backup management API if available
    if BACKUP_API_AVAILABLE:
        app.include_router(backup_router, tags=["backup"])
        backend_log.info("Backup management API routes registered")
    else:
        backend_log.warning("Backup management API routes not available")
    
    # Find and set cache middleware for admin operations
    for middleware in app.user_middleware:
        if hasattr(middleware, 'cls') and hasattr(middleware.cls, '__name__') and middleware.cls.__name__ == 'ApiCacheMiddleware':
            # Set the cache middleware instance for admin routes
            cache.set_cache_middleware(middleware)
            break
    app.include_router(user_settings.router)
    app.include_router(audio.router)
    app.include_router(tts.router)

    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR, html=True), name="uploads")
    app.mount(
        "/transcripts",
        StaticFiles(directory=TRANSCRIPTS_DIR, html=True),
        name="transcripts",
    )

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", CacheBustingStaticFiles(directory=static_dir), name="static")
    
    # Mount assets directory for frontend with cache busting
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", CacheBustingStaticFiles(directory=assets_dir), name="assets")

    @app.get("/vite.svg", include_in_schema=False)
    def vite_icon():
        vite_path = static_dir / "vite.svg"
        if vite_path.exists():
            response = FileResponse(vite_path)
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        raise HTTPException(status_code=404, detail="File not found")

    @app.get("/", include_in_schema=False)
    def spa_index():
        response = FileResponse(static_dir / "index.html")
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        backend_log.debug(f"SPA Fallback called with path: {full_path}")
        
        protected = (
            "static",
            "uploads",
            "transcripts",
            "jobs",
            "log",
            "admin/files",
            "admin/reset",
            "admin/download-all",
            "admin/shutdown",
            "admin/restart",
            "health",
            "docs",
            "openapi.json",
        )
        
        # Block sensitive files and directories - check exact matches and startswith
        sensitive_files = {".env", "requirements.txt", "Dockerfile", "docker-compose.yml", "pyproject.toml"}
        sensitive_dirs = {"api/"}
        
        # Check protection
        is_protected = full_path.startswith(protected)
        is_sensitive_file = full_path in sensitive_files
        is_sensitive_dir = any(full_path.startswith(pattern) for pattern in sensitive_dirs)
        
        backend_log.debug(f"Path '{full_path}' - protected: {is_protected}, sensitive_file: {is_sensitive_file}, sensitive_dir: {is_sensitive_dir}")
        
        if is_protected or is_sensitive_file or is_sensitive_dir:
            backend_log.debug(f"Blocking access to protected path: {full_path}")
            raise HTTPException(status_code=404, detail="Not Found")
        
        backend_log.debug(f"Serving SPA for path: {full_path}")
        response = FileResponse(static_dir / "index.html")
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    if backend_log.isEnabledFor(logging.DEBUG):
        backend_log.debug("\nSTATIC ROUTE CHECK:")
        for route in app.routes:
            backend_log.debug(
                f"Path: {getattr(route, 'path', 'n/a')}  →  Name: {getattr(route, 'name', 'n/a')}  →  Type: {type(route)}"
            )
