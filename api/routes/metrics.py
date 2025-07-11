from fastapi import APIRouter, Response, Request, Depends
from api.routes.auth import require_admin

from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

# Import metrics so they are registered on startup
from api.services import job_queue  # noqa: F401

router = APIRouter()


@router.get("/metrics")
def metrics(request: Request, user=Depends(require_admin)) -> Response:
    """Return Prometheus metrics."""
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
