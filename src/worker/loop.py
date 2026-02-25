"""Worker loop for pending job execution and interruption recovery."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Callable

from core.manifest import read_current_stage
from core.pipeline import run_pipeline
from core.pipeline_types import PipelineSettings
from models.database import (
    get_job,
    fetch_pending_jobs,
    get_book,
    init_db,
    mark_job_done,
    mark_job_failed,
    mark_job_running,
    mark_running_jobs_failed,
    update_book_status,
)

PipelineRunner = Callable[..., object]


@dataclass
class WorkerLoop:
    db_path: Path
    workspace_books_dir: Path
    poll_interval_sec: float = 5.0
    pipeline_runner: PipelineRunner = run_pipeline

    def initialize(self) -> None:
        init_db(self.db_path)

    def recover_interrupted(self, message: str = "Interrupted - abnormal termination") -> int:
        return mark_running_jobs_failed(self.db_path, message)

    def process_once(self, now_iso: str | None = None) -> bool:
        pending_jobs = fetch_pending_jobs(self.db_path, now_iso=now_iso, limit=1)
        if not pending_jobs:
            return False

        self._execute_job(pending_jobs[0])
        return True

    def process_job(self, job_id: str) -> bool:
        job = get_job(self.db_path, job_id)
        if job is None:
            return False
        if job.status != "pending":
            return False
        self._execute_job(job)
        return True

    def _execute_job(self, job) -> None:
        book = get_book(self.db_path, job.book_id)
        if book is None:
            mark_job_failed(self.db_path, job.id, f"Book not found: {job.book_id}")
            return

        mark_job_running(self.db_path, job.id)
        update_book_status(self.db_path, book.id, status="running")

        settings = PipelineSettings(
            language=book.ocr_language,
            optimize_mode=book.optimize_mode,
            error_policy=book.error_policy,
            front_cover=book.front_cover,
            back_cover=book.back_cover,
        )

        try:
            self.pipeline_runner(
                input_dir=Path(book.source_path),
                workspace_dir=self.workspace_books_dir,
                settings=settings,
                book_id=book.id,
                resume=job.resume,
            )
            mark_job_done(self.db_path, job.id)
            update_book_status(self.db_path, book.id, status="done", current_stage="finalize")
        except Exception as error:
            mark_job_failed(self.db_path, job.id, str(error))
            manifest_path = Path(book.book_dir) / "manifest.json"
            current_stage = read_current_stage(manifest_path) if manifest_path.exists() else None
            update_book_status(self.db_path, book.id, status="failed", current_stage=current_stage)

    def run(self, max_iterations: int | None = None) -> None:
        self.initialize()
        iterations = 0
        while True:
            if max_iterations is not None and iterations >= max_iterations:
                return
            processed = self.process_once(now_iso=datetime.now(timezone.utc).isoformat())
            if not processed:
                time.sleep(self.poll_interval_sec)
            iterations += 1
