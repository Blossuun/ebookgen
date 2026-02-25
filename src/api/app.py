"""FastAPI application factory for ebookgen."""

from __future__ import annotations

from pathlib import Path
import threading
from typing import Any

from fastapi import FastAPI

from api.routes.books import router as books_router
from api.routes.jobs import router as jobs_router
from api.routes.ws import router as ws_router
from models.database import init_db
from worker.loop import WorkerLoop


def create_app(*, books_root: Path = Path("workspace/books"), db_path: Path | None = None) -> FastAPI:
    resolved_books_root = books_root.resolve()
    resolved_books_root.mkdir(parents=True, exist_ok=True)
    resolved_db_path = db_path.resolve() if db_path is not None else resolved_books_root.parent / "db.sqlite"
    init_db(resolved_db_path)

    worker = WorkerLoop(db_path=resolved_db_path, workspace_books_dir=resolved_books_root)
    worker.initialize()

    app = FastAPI(title="ebookgen API", version="0.3.0")
    app.state.books_root = resolved_books_root
    app.state.db_path = resolved_db_path
    app.state.worker = worker
    app.state.background_jobs: dict[str, Any] = {}
    app.state.ws_connection_limit = 100
    app.state.ws_max_connection_sec = 600.0
    app.state.ws_active_connections = 0
    app.state.ws_connection_lock = threading.Lock()

    app.include_router(books_router)
    app.include_router(jobs_router)
    app.include_router(ws_router)

    return app


app = create_app()
