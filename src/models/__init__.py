"""Data model package for ebookgen."""

from models.database import (
    create_book,
    create_job,
    fetch_pending_jobs,
    find_latest_failed_book_by_source,
    get_book,
    get_job,
    init_db,
    list_books,
    mark_job_done,
    mark_job_failed,
    mark_job_running,
    update_book_status,
)
from models.schemas import Book, Job

__all__ = [
    "Book",
    "Job",
    "init_db",
    "create_book",
    "get_book",
    "list_books",
    "update_book_status",
    "create_job",
    "get_job",
    "fetch_pending_jobs",
    "mark_job_running",
    "mark_job_done",
    "mark_job_failed",
    "find_latest_failed_book_by_source",
]
