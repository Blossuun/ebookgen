"""SQLite row schemas used by the persistence layer."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3


@dataclass(frozen=True)
class Book:
    id: str
    title: str
    source_path: str
    book_dir: str
    status: str
    current_stage: str
    ocr_language: str
    optimize_mode: str
    error_policy: str
    front_cover: int | None
    back_cover: int | None
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Book":
        return cls(
            id=row["id"],
            title=row["title"],
            source_path=row["source_path"],
            book_dir=row["book_dir"],
            status=row["status"],
            current_stage=row["current_stage"],
            ocr_language=row["ocr_language"],
            optimize_mode=row["optimize_mode"],
            error_policy=row["error_policy"],
            front_cover=row["front_cover"],
            back_cover=row["back_cover"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass(frozen=True)
class Job:
    id: str
    book_id: str
    status: str
    scheduled_at: str | None
    started_at: str | None
    finished_at: str | None
    error_message: str | None
    resume: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Job":
        return cls(
            id=row["id"],
            book_id=row["book_id"],
            status=row["status"],
            scheduled_at=row["scheduled_at"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            error_message=row["error_message"],
            resume=bool(row["resume"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

