"""Job execution/status routes."""

from __future__ import annotations

import threading
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_background_jobs, get_db_path, get_worker
from api.schemas import JobCreateRequest, JobCreateResponse, JobResponse, JobRetryRequest
from models.database import cancel_job, create_job, get_book, get_job
from worker.loop import WorkerLoop

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _start_job_in_background(
    *,
    worker: WorkerLoop,
    job_id: str,
    background_jobs: dict[str, threading.Thread],
) -> None:
    if job_id in background_jobs and background_jobs[job_id].is_alive():
        return

    def _run() -> None:
        try:
            worker.process_job(job_id)
        finally:
            background_jobs.pop(job_id, None)

    thread = threading.Thread(target=_run, daemon=True)
    background_jobs[job_id] = thread
    thread.start()


@router.post("", response_model=JobCreateResponse, status_code=201)
def create_job_route(
    request: JobCreateRequest,
    db_path: Path = Depends(get_db_path),
    worker: WorkerLoop = Depends(get_worker),
    background_jobs: dict[str, threading.Thread] = Depends(get_background_jobs),
) -> JobCreateResponse:
    book = get_book(db_path, request.book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    job = create_job(
        db_path,
        book_id=request.book_id,
        scheduled_at=request.scheduled_at,
        resume=request.resume,
    )

    started = False
    if request.run_now and request.scheduled_at is None:
        _start_job_in_background(worker=worker, job_id=job.id, background_jobs=background_jobs)
        started = True

    return JobCreateResponse(job=JobResponse.model_validate(job), started=started)


@router.get("/{job_id}", response_model=JobResponse)
def get_job_route(job_id: str, db_path: Path = Depends(get_db_path)) -> JobResponse:
    job = get_job(db_path, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@router.post("/{job_id}/cancel", response_model=JobResponse)
def cancel_job_route(job_id: str, db_path: Path = Depends(get_db_path)) -> JobResponse:
    existing = get_job(db_path, job_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Job not found")

    cancelled = cancel_job(db_path, job_id)
    if not cancelled:
        raise HTTPException(status_code=409, detail="Job cannot be cancelled")

    updated = get_job(db_path, job_id)
    if updated is None:
        raise HTTPException(status_code=500, detail="Job state unavailable")
    return JobResponse.model_validate(updated)


@router.post("/{job_id}/retry", response_model=JobCreateResponse, status_code=201)
def retry_job_route(
    job_id: str,
    request: JobRetryRequest,
    db_path: Path = Depends(get_db_path),
    worker: WorkerLoop = Depends(get_worker),
    background_jobs: dict[str, threading.Thread] = Depends(get_background_jobs),
) -> JobCreateResponse:
    job = get_job(db_path, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in {"failed", "cancelled"}:
        raise HTTPException(status_code=409, detail="Only failed/cancelled jobs can be retried")

    retry_job = create_job(db_path, book_id=job.book_id, resume=True)

    started = False
    if request.run_now:
        _start_job_in_background(worker=worker, job_id=retry_job.id, background_jobs=background_jobs)
        started = True

    return JobCreateResponse(job=JobResponse.model_validate(retry_job), started=started)

