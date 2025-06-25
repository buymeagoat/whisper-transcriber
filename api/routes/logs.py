from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from api.errors import ErrorCode, http_error
from api.paths import storage, LOG_DIR
from api.app_state import ACCESS_LOG, backend_log

router = APIRouter()


@router.get("/log/{job_id}", response_class=PlainTextResponse)
def get_job_log(job_id: str):
    log_path = LOG_DIR / f"{job_id}.log"
    if not log_path.exists():
        return PlainTextResponse("No log yet.", status_code=404)
    return log_path.read_text(encoding="utf-8")


@router.post("/log_event")
async def log_event(request: Request):
    try:
        payload = await request.json()
        event = payload.get("event", "unknown")
        context = payload.get("context", {})
        backend_log.info(f"Client Event: {event} | Context: {context}")
        return {"status": "logged"}
    except Exception as e:
        backend_log.error(f"Failed to log client event: {e}")
        return {"status": "error", "message": str(e)}


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
