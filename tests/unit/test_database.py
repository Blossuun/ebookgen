from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from models.database import (
    create_book,
    create_job,
    fetch_pending_jobs,
    get_book,
    init_db,
    update_book_status,
)


def test_create_book(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    init_db(db_path)
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    book = create_book(db_path, source_path=source_dir, book_dir=tmp_path / "books")
    assert book.id
    assert book.title == "source"
    assert Path(book.source_path) == source_dir.resolve()


def test_update_book_status(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    init_db(db_path)
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    book = create_book(db_path, source_path=source_dir, book_dir=tmp_path / "books")

    update_book_status(db_path, book.id, status="running", current_stage="ocr")
    updated = get_book(db_path, book.id)
    assert updated is not None
    assert updated.status == "running"
    assert updated.current_stage == "ocr"


def test_create_job(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    init_db(db_path)
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    book = create_book(db_path, source_path=source_dir, book_dir=tmp_path / "books")

    job = create_job(db_path, book_id=book.id, resume=True)
    assert job.book_id == book.id
    assert job.status == "pending"
    assert job.resume is True


def test_fetch_pending_jobs(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    init_db(db_path)
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    book = create_book(db_path, source_path=source_dir, book_dir=tmp_path / "books")

    now = datetime.now(timezone.utc)
    create_job(db_path, book_id=book.id, scheduled_at=(now + timedelta(minutes=10)).isoformat())
    eligible = create_job(db_path, book_id=book.id, scheduled_at=(now - timedelta(minutes=1)).isoformat())

    pending = fetch_pending_jobs(db_path, now_iso=now.isoformat(), limit=10)
    assert [job.id for job in pending] == [eligible.id]

