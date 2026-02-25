"""Book CRUD and preview routes."""

from __future__ import annotations

from pathlib import Path
import shutil

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_books_root, get_db_path
from api.schemas import (
    BookCreateRequest,
    BookDetailResponse,
    BookPatchRequest,
    BookPreviewResponse,
    BookResponse,
)
from core.manifest import read_manifest
from models.database import (
    create_book,
    delete_book,
    get_book,
    list_books,
    update_book_settings,
)

router = APIRouter(prefix="/api/books", tags=["books"])

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


@router.get("", response_model=list[BookResponse])
def list_books_route(db_path: Path = Depends(get_db_path)) -> list[BookResponse]:
    books = list_books(db_path)
    return [BookResponse.model_validate(book) for book in books]


@router.get("/{book_id}", response_model=BookDetailResponse)
def get_book_route(book_id: str, db_path: Path = Depends(get_db_path)) -> BookDetailResponse:
    book = get_book(db_path, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    manifest_path = Path(book.book_dir) / "manifest.json"
    manifest = read_manifest(manifest_path) if manifest_path.exists() else None
    payload = BookDetailResponse.model_validate(book).model_dump()
    payload["manifest"] = manifest
    return BookDetailResponse.model_validate(payload)


@router.post("", response_model=BookResponse, status_code=201)
def create_book_route(
    request: BookCreateRequest,
    db_path: Path = Depends(get_db_path),
    books_root: Path = Depends(get_books_root),
) -> BookResponse:
    source_path = Path(request.path).resolve()
    if not source_path.exists() or not source_path.is_dir():
        raise HTTPException(status_code=400, detail="Invalid source directory path")

    book = create_book(
        db_path,
        source_path=source_path,
        book_dir=books_root,
        title=request.title,
        ocr_language=request.ocr_language,
        optimize_mode=request.optimize_mode,
        error_policy=request.error_policy,
        front_cover=request.front_cover,
        back_cover=request.back_cover,
    )
    return BookResponse.model_validate(book)


@router.patch("/{book_id}", response_model=BookResponse)
def patch_book_route(
    book_id: str,
    request: BookPatchRequest,
    db_path: Path = Depends(get_db_path),
) -> BookResponse:
    book = update_book_settings(
        db_path,
        book_id,
        ocr_language=request.ocr_language,
        optimize_mode=request.optimize_mode,
        error_policy=request.error_policy,
        front_cover=request.front_cover,
        back_cover=request.back_cover,
    )
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return BookResponse.model_validate(book)


@router.delete("/{book_id}", status_code=204)
def delete_book_route(book_id: str, db_path: Path = Depends(get_db_path)) -> None:
    book = get_book(db_path, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    removed = delete_book(db_path, book_id)
    if not removed:
        raise HTTPException(status_code=500, detail="Failed to delete book")

    book_dir = Path(book.book_dir)
    if book_dir.exists():
        shutil.rmtree(book_dir)


@router.get("/{book_id}/preview", response_model=BookPreviewResponse)
def preview_book_route(book_id: str, db_path: Path = Depends(get_db_path)) -> BookPreviewResponse:
    book = get_book(db_path, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    input_dir = Path(book.book_dir) / "input"
    if not input_dir.exists():
        input_dir = Path(book.source_path)
    if not input_dir.exists() or not input_dir.is_dir():
        raise HTTPException(status_code=404, detail="Input directory not found")

    files = sorted(
        [
            path.name
            for path in input_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        ]
    )
    if not files:
        raise HTTPException(status_code=404, detail="No preview images found")

    return BookPreviewResponse(front=files[:5], back=files[-5:])

