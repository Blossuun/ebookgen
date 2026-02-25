"""WebSocket route for job progress updates."""

from __future__ import annotations

import asyncio
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


@router.websocket("/ws/jobs/{job_id}")
async def job_progress_ws(
    websocket: WebSocket,
    job_id: str,
    db_path: Path = Depends(get_db_path),
) -> None:
    await websocket.accept()
    last_state: tuple[str, str] | None = None

    try:
        while True:
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

