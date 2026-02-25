from __future__ import annotations

from pathlib import Path

from models.database import (
    create_book,
    create_job,
    get_book,
    get_job,
    init_db,
    mark_job_running,
    update_book_status,
)
from worker.loop import WorkerLoop


def test_worker_picks_pending_job(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    books_root = tmp_path / "books"
    books_root.mkdir(parents=True)
    init_db(db_path)

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    book = create_book(db_path, source_path=source_dir, book_dir=books_root)
    create_job(db_path, book_id=book.id)

    worker = WorkerLoop(db_path=db_path, workspace_books_dir=books_root, pipeline_runner=lambda **_: None)
    processed = worker.process_once()
    assert processed is True


def test_worker_marks_done_on_success(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    books_root = tmp_path / "books"
    books_root.mkdir(parents=True)
    init_db(db_path)

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    book = create_book(db_path, source_path=source_dir, book_dir=books_root)
    job = create_job(db_path, book_id=book.id)

    worker = WorkerLoop(db_path=db_path, workspace_books_dir=books_root, pipeline_runner=lambda **_: None)
    worker.process_once()

    job_state = get_job(db_path, job.id)
    assert job_state is not None
    assert job_state.status == "done"


def test_worker_marks_failed_on_error(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    books_root = tmp_path / "books"
    books_root.mkdir(parents=True)
    init_db(db_path)

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    book = create_book(db_path, source_path=source_dir, book_dir=books_root)
    job = create_job(db_path, book_id=book.id)

    def _raise_error(**_: object) -> None:
        raise RuntimeError("pipeline failed")

    worker = WorkerLoop(db_path=db_path, workspace_books_dir=books_root, pipeline_runner=_raise_error)
    worker.process_once()

    job_state = get_job(db_path, job.id)
    assert job_state is not None
    assert job_state.status == "failed"
    assert "pipeline failed" in (job_state.error_message or "")


def test_worker_recovers_interrupted(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    books_root = tmp_path / "books"
    books_root.mkdir(parents=True)
    init_db(db_path)

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    book = create_book(db_path, source_path=source_dir, book_dir=books_root)
    job = create_job(db_path, book_id=book.id)

    mark_job_running(db_path, job.id)
    update_book_status(db_path, book.id, status="running")

    worker = WorkerLoop(db_path=db_path, workspace_books_dir=books_root, pipeline_runner=lambda **_: None)
    recovered = worker.recover_interrupted()
    assert recovered == 1

    job_state = get_job(db_path, job.id)
    book_state = get_book(db_path, book.id)
    assert job_state is not None and job_state.status == "failed"
    assert book_state is not None and book_state.status == "failed"


def test_worker_idle_when_no_jobs(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    books_root = tmp_path / "books"
    books_root.mkdir(parents=True)
    init_db(db_path)

    worker = WorkerLoop(db_path=db_path, workspace_books_dir=books_root, pipeline_runner=lambda **_: None)
    assert worker.process_once() is False

