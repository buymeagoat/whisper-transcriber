from fastapi import APIRouter, Response, Request, HTTPException, status

from api import config
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

router = APIRouter()


@router.get("/metrics")
def metrics(request: Request) -> Response:
    """Return Prometheus metrics."""
    token = config.METRICS_TOKEN
    if token:
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        if auth.split(" ", 1)[1] != token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
