from __future__ import annotations

import asyncio
from typing import Dict, Set

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from api.routes.auth import get_current_user
from api.models import User

router = APIRouter()

# Store active websocket connections per job id
progress_connections: Dict[str, Set[WebSocket]] = {}


async def _broadcast(job_id: str, status: str) -> None:
    """Send a status update to all websockets for this job."""
    websockets = progress_connections.get(job_id)
    if not websockets:
        return
    stale: Set[WebSocket] = set()
    for ws in list(websockets):
        try:
            await ws.send_json({"status": status})
        except Exception:
            stale.add(ws)
    websockets.difference_update(stale)
    if not websockets:
        progress_connections.pop(job_id, None)


def send_progress_update(job_id: str, status: str) -> None:
    """Entry point used by background threads."""
    try:
        asyncio.run(_broadcast(job_id, status))
    except RuntimeError:
        # Called from within event loop; schedule as task
        loop = asyncio.get_event_loop()
        loop.create_task(_broadcast(job_id, status))


@router.websocket("/ws/progress/{job_id}")
async def websocket_progress(
    websocket: WebSocket, job_id: str, user: User = Depends(get_current_user)
) -> None:
    await websocket.accept()
    progress_connections.setdefault(job_id, set()).add(websocket)
    try:
        while True:
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        pass
    finally:
        connections = progress_connections.get(job_id)
        if connections:
            connections.discard(websocket)
            if not connections:
                progress_connections.pop(job_id, None)
