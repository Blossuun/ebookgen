"""Output download route."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from api.deps import get_db_path
from models.database import get_book

router = APIRouter(prefix="/api/output", tags=["output"])

ALLOWED_OUTPUT_FILES = {"book.pdf", "book.txt", "report.json"}


@router.get("/{book_id}/{file_name}")
def download_output_route(
    book_id: str,
    file_name: str,
    db_path: Path = Depends(get_db_path),
) -> FileResponse:
    if file_name not in ALLOWED_OUTPUT_FILES:
        raise HTTPException(status_code=400, detail="Unsupported output file")

    book = get_book(db_path, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    file_path = Path(book.book_dir) / "out" / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(path=file_path, filename=file_name)

