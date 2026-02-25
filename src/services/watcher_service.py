"""Inbox watcher service for auto-importing book folders."""

from __future__ import annotations

from pathlib import Path
import shutil
import threading
import time
from uuid import uuid4

from models.database import create_book, init_db

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def _has_supported_images(directory: Path) -> bool:
    return any(
        child.is_file() and child.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS for child in directory.iterdir()
    )


class InboxWatcherService:
    """Watches inbox and imports newly dropped folders into books workspace."""

    def __init__(
        self,
        *,
        db_path: Path,
        inbox_dir: Path,
        books_root: Path,
        poll_interval_sec: float = 1.0,
    ) -> None:
        self.db_path = db_path.resolve()
        self.inbox_dir = inbox_dir.resolve()
        self.books_root = books_root.resolve()
        self.poll_interval_sec = poll_interval_sec
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def _list_candidate_dirs(self) -> list[Path]:
        if not self.inbox_dir.exists():
            return []
        return sorted(
            [
                child
                for child in self.inbox_dir.iterdir()
                if child.is_dir() and not child.name.startswith(".")
            ],
            key=lambda path: path.name,
        )

    def scan_once(self) -> list[str]:
        """Detect and import new folders once. Returns imported book IDs."""
        init_db(self.db_path)
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.books_root.mkdir(parents=True, exist_ok=True)

        imported: list[str] = []
        for source_dir in self._list_candidate_dirs():
            if not _has_supported_images(source_dir):
                continue

            book_id = uuid4().hex[:12]
            destination_input = self.books_root / book_id / "input"
            destination_input.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_dir), str(destination_input))

            create_book(
                self.db_path,
                source_path=destination_input,
                book_dir=self.books_root,
                title=source_dir.name,
                book_id=book_id,
            )
            imported.append(book_id)

        return imported

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()

        def _run() -> None:
            while not self._stop_event.is_set():
                try:
                    self.scan_once()
                except Exception:
                    # Keep watcher alive even if a single import fails.
                    pass
                self._stop_event.wait(self.poll_interval_sec)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._thread = None

