from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import jobs, admin, logs, metrics, auth, users
from api.routes import progress
from api.paths import storage, UPLOAD_DIR, TRANSCRIPTS_DIR
from api.app_state import backend_log


def register_routes(app: FastAPI) -> None:
    """Attach all API routers and static paths."""
    app.include_router(jobs.router)
    app.include_router(admin.router)
    app.include_router(logs.router)
    app.include_router(progress.router)
    app.include_router(metrics.router)
    app.include_router(auth.router)
    app.include_router(users.router)

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

    backend_log.debug("\nSTATIC ROUTE CHECK:")
    for route in app.routes:
        backend_log.debug(
            f"Path: {getattr(route, 'path', 'n/a')}  →  Name: {getattr(route, 'name', 'n/a')}  →  Type: {type(route)}"
        )
