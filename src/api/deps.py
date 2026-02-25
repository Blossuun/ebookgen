"""FastAPI dependency helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from starlette.requests import HTTPConnection

from worker.loop import WorkerLoop


def get_db_path(conn: HTTPConnection) -> Path:
    return conn.app.state.db_path


def get_books_root(conn: HTTPConnection) -> Path:
    return conn.app.state.books_root


def get_worker(conn: HTTPConnection) -> WorkerLoop:
    return conn.app.state.worker


def get_background_jobs(conn: HTTPConnection) -> dict[str, Any]:
    return conn.app.state.background_jobs
