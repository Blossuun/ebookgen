"""FastAPI application factory for ebookgen."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
import threading
from typing import Any, Callable

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.pipeline import run_pipeline
from api.routes.books import router as books_router
from api.routes.jobs import router as jobs_router
from api.routes.output import router as output_router
from api.routes.ws import router as ws_router
from models.database import init_db
from services.watcher_service import InboxWatcherService
from worker.loop import WorkerLoop


def create_app(
    *,
    books_root: Path = Path("workspace/books"),
    db_path: Path | None = None,
    inbox_root: Path | None = None,
    enable_watcher: bool = True,
    pipeline_runner: Callable[..., object] = run_pipeline,
) -> FastAPI:
    resolved_books_root = books_root.resolve()
    resolved_books_root.mkdir(parents=True, exist_ok=True)
    resolved_db_path = db_path.resolve() if db_path is not None else resolved_books_root.parent / "db.sqlite"
    resolved_inbox_root = (
        inbox_root.resolve() if inbox_root is not None else resolved_books_root.parent / "inbox"
    )
    resolved_inbox_root.mkdir(parents=True, exist_ok=True)
    init_db(resolved_db_path)

    worker = WorkerLoop(
        db_path=resolved_db_path,
        workspace_books_dir=resolved_books_root,
        pipeline_runner=pipeline_runner,
    )
    worker.initialize()
    watcher = InboxWatcherService(
        db_path=resolved_db_path,
        inbox_dir=resolved_inbox_root,
        books_root=resolved_books_root,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if enable_watcher:
            watcher.start()
        try:
            yield
        finally:
            watcher.stop()

    app = FastAPI(title="ebookgen API", version="0.4.0", lifespan=lifespan)
    app.state.books_root = resolved_books_root
    app.state.db_path = resolved_db_path
    app.state.inbox_root = resolved_inbox_root
    app.state.worker = worker
    app.state.watcher = watcher
    app.state.background_jobs: dict[str, Any] = {}
    app.state.ws_connection_limit = 100
    app.state.ws_max_connection_sec = 600.0
    app.state.ws_active_connections = 0
    app.state.ws_connection_lock = threading.Lock()

    app.include_router(books_router)
    app.include_router(jobs_router)
    app.include_router(output_router)
    app.include_router(ws_router)

    frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    return app


app = create_app()
