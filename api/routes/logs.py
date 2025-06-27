from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Depends
from api.routes.auth import get_current_user
from api.models import User
import asyncio
from fastapi.responses import PlainTextResponse

from api.errors import ErrorCode, http_error
from api.paths import storage, LOG_DIR
from api.app_state import ACCESS_LOG, backend_log
from api.schemas import StatusOut

router = APIRouter()


@router.get("/log/{job_id}", response_class=PlainTextResponse)
def get_job_log(job_id: str):
    log_path = LOG_DIR / f"{job_id}.log"
    if not log_path.exists():
        return PlainTextResponse("No log yet.", status_code=404)
    return log_path.read_text(encoding="utf-8")


@router.websocket("/ws/logs/{job_id}")
async def websocket_job_log(
    websocket: WebSocket, job_id: str, user: User = Depends(get_current_user)
):
    await websocket.accept()
    log_path = LOG_DIR / f"{job_id}.log"
    position = 0
    try:
        while True:
            if log_path.exists():
                with log_path.open("r", encoding="utf-8") as f:
                    f.seek(position)
                    data = f.read()
                    if data:
                        await websocket.send_text(data)
                        position = f.tell()
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass


@router.websocket("/ws/logs/system")
async def websocket_system_log(
    websocket: WebSocket, user: User = Depends(get_current_user)
):
    """Stream the access log or fallback system log to the client."""
    await websocket.accept()
    position = 0
    try:
        while True:
            log_path = ACCESS_LOG if ACCESS_LOG.exists() else LOG_DIR / "system.log"
            if log_path.exists():
                with log_path.open("r", encoding="utf-8") as f:
                    f.seek(position)
                    data = f.read()
                    if data:
                        await websocket.send_text(data)
                        position = f.tell()
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass


@router.post("/log_event", response_model=StatusOut)
async def log_event(request: Request) -> StatusOut:
    try:
        payload = await request.json()
        event = payload.get("event", "unknown")
        context = payload.get("context", {})
        backend_log.info(f"Client Event: {event} | Context: {context}")
        return StatusOut(status="logged")
    except Exception as e:
        backend_log.error(f"Failed to log client event: {e}")
        return StatusOut(status="error", message=str(e))


@router.get("/logs/access", response_class=PlainTextResponse)
def get_access_log():
    if not ACCESS_LOG.exists():
        return PlainTextResponse("", status_code=404)
    return ACCESS_LOG.read_text()


@router.get("/logs/{filename}", response_class=PlainTextResponse)
def get_log_file(filename: str):
    path = LOG_DIR / filename
    if not path.exists():
        raise http_error(ErrorCode.FILE_NOT_FOUND)
    return path.read_text()
