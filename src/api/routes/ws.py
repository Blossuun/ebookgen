"""WebSocket route for job progress updates."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from api.deps import get_db_path
from models.database import get_book, get_job

router = APIRouter(tags=["ws"])

STAGE_PERCENT = {
    "validate": 20,
    "assemble": 40,
    "ocr": 60,
    "optimize": 80,
    "finalize": 100,
}


def _progress_payload(*, job_id: str, job_status: str, stage: str) -> dict[str, object]:
    percent = STAGE_PERCENT.get(stage, 0)
    if job_status == "done":
        percent = 100
    return {
        "type": "progress",
        "job_id": job_id,
        "status": job_status,
        "step_name": stage,
        "percent": percent,
    }


def _completion_payload(*, job_id: str, job_status: str) -> dict[str, object]:
    return {"type": "completion", "job_id": job_id, "status": job_status}


def _try_acquire_ws_slot(websocket: WebSocket) -> bool:
    lock = websocket.app.state.ws_connection_lock
    with lock:
        active = websocket.app.state.ws_active_connections
        limit = websocket.app.state.ws_connection_limit
        if active >= limit:
            return False
        websocket.app.state.ws_active_connections = active + 1
        return True


def _release_ws_slot(websocket: WebSocket) -> None:
    lock = websocket.app.state.ws_connection_lock
    with lock:
        active = websocket.app.state.ws_active_connections
        websocket.app.state.ws_active_connections = max(0, active - 1)


@router.websocket("/ws/jobs/{job_id}")
async def job_progress_ws(
    websocket: WebSocket,
    job_id: str,
    db_path: Path = Depends(get_db_path),
) -> None:
    if not _try_acquire_ws_slot(websocket):
        await websocket.close(code=1013)
        return

    await websocket.accept()
    last_state: tuple[str, str] | None = None
    started_at = time.monotonic()
    max_connection_sec = float(getattr(websocket.app.state, "ws_max_connection_sec", 600.0))

    try:
        while True:
            if time.monotonic() - started_at > max_connection_sec:
                await websocket.send_json({"type": "error", "message": "WebSocket session timed out"})
                await websocket.close(code=1000)
                return

            job = get_job(db_path, job_id)
            if job is None:
                await websocket.send_json({"type": "error", "message": "Job not found"})
                await websocket.close(code=1008)
                return

            book = get_book(db_path, job.book_id)
            stage = book.current_stage if book is not None else "validate"
            state = (job.status, stage)

            if state != last_state:
                await websocket.send_json(
                    _progress_payload(job_id=job_id, job_status=job.status, stage=stage)
                )
                last_state = state

            if job.status in {"done", "failed", "cancelled"}:
                await websocket.send_json(_completion_payload(job_id=job_id, job_status=job.status))
                return

            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        return
    finally:
        _release_ws_slot(websocket)
