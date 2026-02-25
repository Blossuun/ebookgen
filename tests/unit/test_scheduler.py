from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from typer.testing import CliRunner

from cli.main import app
from models.database import (
    create_book,
    create_job,
    get_job,
    init_db,
    list_jobs,
)
from worker.loop import WorkerLoop

runner = CliRunner()


def test_scheduled_job_triggers_at_time(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    books_root = tmp_path / "books"
    books_root.mkdir(parents=True)
    init_db(db_path)

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    book = create_book(db_path, source_path=source_dir, book_dir=books_root)

    now = datetime.now(timezone.utc)
    scheduled_at = (now + timedelta(minutes=5)).isoformat()
    job = create_job(db_path, book_id=book.id, scheduled_at=scheduled_at)

    worker = WorkerLoop(db_path=db_path, workspace_books_dir=books_root, pipeline_runner=lambda **_: None)
    assert worker.process_once(now_iso=now.isoformat()) is False
    assert worker.process_once(now_iso=(now + timedelta(minutes=10)).isoformat()) is True

    job_state = get_job(db_path, job.id)
    assert job_state is not None and job_state.status == "done"


def test_batch_creates_multiple_jobs(tmp_path: Path) -> None:
    batch_root = tmp_path / "batch"
    (batch_root / "book_a").mkdir(parents=True)
    (batch_root / "book_b").mkdir(parents=True)
    output_root = tmp_path / "books"

    result = runner.invoke(app, ["batch", str(batch_root), "--output", str(output_root)])
    assert result.exit_code == 0
    assert "queued_jobs: 2" in result.stdout

    db_path = output_root.resolve().parent / "db.sqlite"
    jobs = list_jobs(db_path)
    assert len(jobs) == 2
    assert all(job.status == "pending" for job in jobs)

