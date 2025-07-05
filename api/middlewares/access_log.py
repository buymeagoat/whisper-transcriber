from datetime import datetime
import time
from fastapi import Request

from api.app_state import LOCAL_TZ, ACCESS_LOG, backend_log


async def access_logger(request: Request, call_next):
    """Log each request/response pair with timing information."""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    host = getattr(request.client, "host", "localtest")
    try:
        with ACCESS_LOG.open("a", encoding="utf-8") as fh:
            fh.write(
                f"[{datetime.now(LOCAL_TZ).isoformat()}] {host} "
                f"{request.method} {request.url.path} -> "
                f"{response.status_code} in {duration:.2f}s\n"
            )
    except OSError as exc:  # pragma: no cover - log failures shouldn't break response
        backend_log.warning(f"Failed to write access log: {exc}")
    return response
