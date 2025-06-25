from fastapi import APIRouter, Response, Request, Depends
from api.routes.auth import get_current_user

from api import config
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

router = APIRouter()


@router.get("/metrics")
def metrics(request: Request, user: str = Depends(get_current_user)) -> Response:
    """Return Prometheus metrics."""
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
