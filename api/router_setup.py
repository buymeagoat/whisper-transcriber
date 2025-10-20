from pathlib import Path
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import jobs, admin, logs, metrics, auth, users, audit, cache
from api.routes import progress, audio, tts, user_settings, enhanced_cache
from api.routes import websockets, admin_websocket, admin_database_optimization
from api.routes import chunked_uploads, upload_websockets, admin_chunked_uploads
from api.paths import storage, UPLOAD_DIR, TRANSCRIPTS_DIR
from api.app_state import backend_log

# Import backup API router
try:
    from app.backup_api import backup_router
    BACKUP_API_AVAILABLE = True
except ImportError as e:
    backend_log.warning(f"Backup API not available: {e}")
    BACKUP_API_AVAILABLE = False


def register_routes(app: FastAPI) -> None:
    """Attach all API routers and static paths."""
    app.include_router(jobs.router)
    app.include_router(admin.router)
    app.include_router(logs.router)
    app.include_router(progress.router)
    app.include_router(metrics.router)
    app.include_router(auth.router)
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
    
    # Include backup management API if available
    if BACKUP_API_AVAILABLE:
        app.include_router(backup_router, tags=["backup"])
        backend_log.info("Backup management API routes registered")
    else:
        backend_log.warning("Backup management API routes not available")
    
    # Find and set cache middleware for admin operations
    for middleware in app.user_middleware:
        if hasattr(middleware, 'cls') and middleware.cls.__name__ == 'ApiCacheMiddleware':
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
    app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")

    @app.get("/", include_in_schema=False)
    def spa_index():
        return FileResponse(static_dir / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
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
        if full_path.startswith(protected):
            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(static_dir / "index.html")

    if backend_log.isEnabledFor(logging.DEBUG):
        backend_log.debug("\nSTATIC ROUTE CHECK:")
        for route in app.routes:
            backend_log.debug(
                f"Path: {getattr(route, 'path', 'n/a')}  →  Name: {getattr(route, 'name', 'n/a')}  →  Type: {type(route)}"
            )
