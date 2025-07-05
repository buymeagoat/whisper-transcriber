from __future__ import annotations

import asyncio
import threading
from typing import Dict, Set

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from api.routes.auth import get_current_user
from api.models import User

router = APIRouter()

# Store active websocket connections per job id
progress_connections: Dict[str, Set[WebSocket]] = {}
progress_lock = threading.Lock()


async def _broadcast(job_id: str, status: str) -> None:
    """Send a status update to all websockets for this job."""
    with progress_lock:
        websockets = progress_connections.get(job_id)
        if not websockets:
            return
        targets = set(websockets)
    stale: Set[WebSocket] = set()
    for ws in list(targets):
        try:
            await ws.send_json({"status": status})
        except Exception:
            stale.add(ws)
    if stale:
        with progress_lock:
            conns = progress_connections.get(job_id)
            if conns:
                conns.difference_update(stale)
                if not conns:
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
    with progress_lock:
        progress_connections.setdefault(job_id, set()).add(websocket)
    try:
        while True:
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        pass
    finally:
        with progress_lock:
            connections = progress_connections.get(job_id)
            if connections:
                connections.discard(websocket)
                if not connections:
                    progress_connections.pop(job_id, None)
