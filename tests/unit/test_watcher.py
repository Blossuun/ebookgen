from __future__ import annotations

from pathlib import Path

from PIL import Image

from models.database import get_book, init_db, list_books
from services.watcher_service import InboxWatcherService


def _create_inbox_book(inbox_dir: Path, folder_name: str = "book_from_inbox") -> Path:
    source = inbox_dir / folder_name
    source.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (120, 160), color=(220, 220, 220))
    image.save(source / "0001.jpg", format="JPEG")
    image.close()
    return source


def test_new_folder_detected(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    inbox_dir = tmp_path / "inbox"
    books_root = tmp_path / "books"
    init_db(db_path)
    _create_inbox_book(inbox_dir)

    watcher = InboxWatcherService(db_path=db_path, inbox_dir=inbox_dir, books_root=books_root)
    imported = watcher.scan_once()
    assert len(imported) == 1


def test_folder_moved_to_books(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    inbox_dir = tmp_path / "inbox"
    books_root = tmp_path / "books"
    init_db(db_path)
    source_dir = _create_inbox_book(inbox_dir)

    watcher = InboxWatcherService(db_path=db_path, inbox_dir=inbox_dir, books_root=books_root)
    imported = watcher.scan_once()
    assert len(imported) == 1
    book_id = imported[0]

    assert not source_dir.exists()
    assert (books_root / book_id / "input" / "0001.jpg").exists()


def test_db_entry_created(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    inbox_dir = tmp_path / "inbox"
    books_root = tmp_path / "books"
    init_db(db_path)
    _create_inbox_book(inbox_dir, folder_name="detected_book")

    watcher = InboxWatcherService(db_path=db_path, inbox_dir=inbox_dir, books_root=books_root)
    imported = watcher.scan_once()
    assert len(imported) == 1
    book_id = imported[0]

    books = list_books(db_path)
    assert len(books) == 1
    book = get_book(db_path, book_id)
    assert book is not None
    assert book.title == "detected_book"
    assert Path(book.source_path) == (books_root / book_id / "input").resolve()

