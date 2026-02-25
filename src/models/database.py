"""SQLite persistence for books/jobs state management."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from uuid import uuid4

from models.schemas import Book, Job


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connection(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path) -> None:
    with connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_path TEXT NOT NULL,
                book_dir TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                current_stage TEXT NOT NULL DEFAULT 'validate',
                ocr_language TEXT NOT NULL DEFAULT 'kor+eng',
                optimize_mode TEXT NOT NULL DEFAULT 'basic',
                error_policy TEXT NOT NULL DEFAULT 'skip',
                front_cover INTEGER,
                back_cover INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
                status TEXT NOT NULL DEFAULT 'pending',
                scheduled_at TEXT,
                started_at TEXT,
                finished_at TEXT,
                error_message TEXT,
                resume INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def create_book(
    db_path: Path,
    *,
    source_path: Path,
    book_dir: Path,
    title: str | None = None,
    book_id: str | None = None,
    ocr_language: str = "kor+eng",
    optimize_mode: str = "basic",
    error_policy: str = "skip",
    front_cover: int | None = None,
    back_cover: int | None = None,
) -> Book:
    resolved_source = str(source_path.resolve())
    now = utc_now_iso()
    resolved_book_id = book_id or uuid4().hex[:12]
    resolved_title = title or source_path.name

    resolved_book_dir = (book_dir / resolved_book_id).resolve()

    with connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO books (
                id, title, source_path, book_dir, status, current_stage,
                ocr_language, optimize_mode, error_policy, front_cover, back_cover,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, 'pending', 'validate', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resolved_book_id,
                resolved_title,
                resolved_source,
                str(resolved_book_dir),
                ocr_language,
                optimize_mode,
                error_policy,
                front_cover,
                back_cover,
                now,
                now,
            ),
        )

    book = get_book(db_path, resolved_book_id)
    if book is None:
        raise RuntimeError("Book creation failed.")
    return book


def get_book(db_path: Path, book_id: str) -> Book | None:
    with connection(db_path) as conn:
        row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    return Book.from_row(row) if row is not None else None


def list_books(db_path: Path) -> list[Book]:
    with connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM books ORDER BY created_at DESC").fetchall()
    return [Book.from_row(row) for row in rows]


def find_latest_book_by_source(db_path: Path, source_path: Path) -> Book | None:
    resolved_source = str(source_path.resolve())
    with connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM books WHERE source_path = ? ORDER BY created_at DESC LIMIT 1",
            (resolved_source,),
        ).fetchone()
    return Book.from_row(row) if row is not None else None


def find_latest_failed_book_by_source(db_path: Path, source_path: Path) -> Book | None:
    resolved_source = str(source_path.resolve())
    with connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT * FROM books
            WHERE source_path = ? AND status = 'failed'
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (resolved_source,),
        ).fetchone()
    return Book.from_row(row) if row is not None else None


def update_book_status(
    db_path: Path,
    book_id: str,
    *,
    status: str,
    current_stage: str | None = None,
) -> None:
    now = utc_now_iso()
    with connection(db_path) as conn:
        if current_stage is None:
            conn.execute(
                "UPDATE books SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, book_id),
            )
        else:
            conn.execute(
                "UPDATE books SET status = ?, current_stage = ?, updated_at = ? WHERE id = ?",
                (status, current_stage, now, book_id),
            )


def create_job(
    db_path: Path,
    *,
    book_id: str,
    scheduled_at: str | None = None,
    resume: bool = False,
    job_id: str | None = None,
) -> Job:
    now = utc_now_iso()
    resolved_job_id = job_id or uuid4().hex[:12]
    with connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO jobs (
                id, book_id, status, scheduled_at, started_at, finished_at,
                error_message, resume, created_at, updated_at
            )
            VALUES (?, ?, 'pending', ?, NULL, NULL, NULL, ?, ?, ?)
            """,
            (resolved_job_id, book_id, scheduled_at, int(resume), now, now),
        )
    job = get_job(db_path, resolved_job_id)
    if job is None:
        raise RuntimeError("Job creation failed.")
    return job


def get_job(db_path: Path, job_id: str) -> Job | None:
    with connection(db_path) as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return Job.from_row(row) if row is not None else None


def list_jobs(db_path: Path, status: str | None = None) -> list[Job]:
    with connection(db_path) as conn:
        if status is None:
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC",
                (status,),
            ).fetchall()
    return [Job.from_row(row) for row in rows]


def get_latest_job_for_book(db_path: Path, book_id: str) -> Job | None:
    with connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM jobs WHERE book_id = ? ORDER BY created_at DESC LIMIT 1",
            (book_id,),
        ).fetchone()
    return Job.from_row(row) if row is not None else None


def fetch_pending_jobs(db_path: Path, *, now_iso: str | None = None, limit: int = 1) -> list[Job]:
    now_value = now_iso or utc_now_iso()
    with connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM jobs
            WHERE status = 'pending'
              AND (scheduled_at IS NULL OR scheduled_at <= ?)
            ORDER BY COALESCE(scheduled_at, created_at), created_at
            LIMIT ?
            """,
            (now_value, limit),
        ).fetchall()
    return [Job.from_row(row) for row in rows]


def fetch_running_jobs(db_path: Path) -> list[Job]:
    return list_jobs(db_path, status="running")


def mark_job_running(db_path: Path, job_id: str) -> None:
    now = utc_now_iso()
    with connection(db_path) as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status = 'running', started_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (now, now, job_id),
        )


def mark_job_done(db_path: Path, job_id: str) -> None:
    now = utc_now_iso()
    with connection(db_path) as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status = 'done', finished_at = ?, error_message = NULL, updated_at = ?
            WHERE id = ?
            """,
            (now, now, job_id),
        )


def mark_job_failed(db_path: Path, job_id: str, error_message: str) -> None:
    now = utc_now_iso()
    with connection(db_path) as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status = 'failed', finished_at = ?, error_message = ?, updated_at = ?
            WHERE id = ?
            """,
            (now, error_message, now, job_id),
        )


def mark_running_jobs_failed(db_path: Path, message: str) -> int:
    now = utc_now_iso()
    with connection(db_path) as conn:
        running_rows = conn.execute(
            "SELECT id, book_id FROM jobs WHERE status = 'running'"
        ).fetchall()
        for row in running_rows:
            conn.execute(
                """
                UPDATE jobs
                SET status = 'failed', finished_at = ?, error_message = ?, updated_at = ?
                WHERE id = ?
                """,
                (now, message, now, row["id"]),
            )
            conn.execute(
                """
                UPDATE books
                SET status = 'failed', updated_at = ?
                WHERE id = ?
                """,
                (now, row["book_id"]),
            )
    return len(running_rows)
