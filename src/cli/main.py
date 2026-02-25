"""Typer-based command-line interface for ebookgen."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import typer

from models.database import (
    create_book,
    create_job,
    find_latest_failed_book_by_source,
    get_book,
    get_job,
    get_latest_job_for_book,
    init_db,
    list_books,
    utc_now_iso,
)
from worker.loop import WorkerLoop

app = typer.Typer(
    help="Convert image folders into searchable PDF and text files.",
    no_args_is_help=True,
)


def _default_db_path(books_root: Path) -> Path:
    return books_root.resolve().parent / "db.sqlite"


def _resolve_db_path(books_root: Path, db_path: Path | None) -> Path:
    return db_path.resolve() if db_path is not None else _default_db_path(books_root)


def _resolve_job_schedule(delay_minutes: int) -> str | None:
    if delay_minutes <= 0:
        return None
    return (datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)).isoformat()


def _run_single_job(
    *,
    db_path: Path,
    books_root: Path,
    job_id: str,
) -> None:
    worker = WorkerLoop(db_path=db_path, workspace_books_dir=books_root)
    worker.initialize()
    processed = worker.process_job(job_id)
    if not processed:
        raise typer.Exit(code=1)


@app.callback()
def cli() -> None:
    """ebookgen command group."""


@app.command()
def convert(
    input_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    language: str = typer.Option("kor+eng", "--language", help="OCR language hint."),
    optimize: str = typer.Option("basic", "--optimize", help="basic|balanced|max"),
    output: Path = typer.Option(
        Path("workspace/books"),
        "--output",
        file_okay=False,
        dir_okay=True,
        help="Workspace root for generated book directories.",
    ),
    skip_errors: bool = typer.Option(
        True,
        "--skip-errors/--abort-on-error",
        help="Continue with fallback outputs when OCR fails.",
    ),
    front_cover: int | None = typer.Option(None, "--front-cover"),
    back_cover: int | None = typer.Option(None, "--back-cover"),
    resume: bool = typer.Option(False, "--resume", help="Resume the latest failed job for this input."),
    db: Path | None = typer.Option(None, "--db", file_okay=True, dir_okay=False),
) -> None:
    """Run conversion immediately and persist state/job history in SQLite."""
    books_root = output.resolve()
    books_root.mkdir(parents=True, exist_ok=True)
    db_path = _resolve_db_path(books_root, db)
    init_db(db_path)

    if resume:
        book = find_latest_failed_book_by_source(db_path, input_dir.resolve())
        if book is None:
            raise typer.BadParameter("No failed book found for --resume input.")
        job = create_job(db_path, book_id=book.id, resume=True)
    else:
        book = create_book(
            db_path,
            source_path=input_dir.resolve(),
            book_dir=books_root,
            ocr_language=language,
            optimize_mode=optimize,
            error_policy="skip" if skip_errors else "abort",
            front_cover=front_cover,
            back_cover=back_cover,
        )
        job = create_job(db_path, book_id=book.id, resume=False)

    _run_single_job(db_path=db_path, books_root=books_root, job_id=job.id)

    job_state = get_job(db_path, job.id)
    book_state = get_book(db_path, job.book_id)
    if job_state is None or book_state is None:
        raise typer.Exit(code=1)

    typer.echo(f"book_id: {book_state.id}")
    typer.echo(f"job_id: {job_state.id}")
    typer.echo(f"book_status: {book_state.status}")
    typer.echo(f"job_status: {job_state.status}")
    typer.echo(f"output_dir: {Path(book_state.book_dir)}")

    if job_state.status != "done":
        raise typer.Exit(code=1)


@app.command()
def batch(
    input_root: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    output: Path = typer.Option(
        Path("workspace/books"),
        "--output",
        file_okay=False,
        dir_okay=True,
        help="Workspace root for generated book directories.",
    ),
    language: str = typer.Option("kor+eng", "--language"),
    optimize: str = typer.Option("basic", "--optimize"),
    skip_errors: bool = typer.Option(True, "--skip-errors/--abort-on-error"),
    delay_minutes: int = typer.Option(0, "--delay-minutes", min=0),
    run_now: bool = typer.Option(False, "--run-now/--queue-only"),
    db: Path | None = typer.Option(None, "--db", file_okay=True, dir_okay=False),
) -> None:
    """Create jobs for each subdirectory under input_root; optionally execute immediately."""
    books_root = output.resolve()
    books_root.mkdir(parents=True, exist_ok=True)
    db_path = _resolve_db_path(books_root, db)
    init_db(db_path)

    subdirs = sorted([path for path in input_root.iterdir() if path.is_dir()], key=lambda path: path.name)
    if not subdirs:
        typer.echo("No subdirectories found to batch.")
        return

    scheduled_at = _resolve_job_schedule(delay_minutes)
    created_jobs = []
    for directory in subdirs:
        book = create_book(
            db_path,
            source_path=directory.resolve(),
            book_dir=books_root,
            ocr_language=language,
            optimize_mode=optimize,
            error_policy="skip" if skip_errors else "abort",
        )
        job = create_job(db_path, book_id=book.id, scheduled_at=scheduled_at, resume=False)
        created_jobs.append(job)

    typer.echo(f"queued_jobs: {len(created_jobs)}")
    if run_now and delay_minutes == 0:
        worker = WorkerLoop(db_path=db_path, workspace_books_dir=books_root)
        worker.initialize()
        processed = 0
        now_iso = utc_now_iso()
        while worker.process_once(now_iso=now_iso):
            processed += 1
        typer.echo(f"processed_jobs: {processed}")


@app.command()
def status(
    output: Path = typer.Option(
        Path("workspace/books"),
        "--output",
        file_okay=False,
        dir_okay=True,
        help="Workspace root for generated book directories.",
    ),
    db: Path | None = typer.Option(None, "--db", file_okay=True, dir_okay=False),
) -> None:
    """Print books and latest job status."""
    books_root = output.resolve()
    db_path = _resolve_db_path(books_root, db)
    init_db(db_path)

    books = list_books(db_path)
    if not books:
        typer.echo("No books found.")
        return

    for book in books:
        latest_job = get_latest_job_for_book(db_path, book.id)
        latest_job_status = latest_job.status if latest_job else "-"
        typer.echo(
            f"{book.title} ({book.id}) | book={book.status} | stage={book.current_stage} | "
            f"latest_job={latest_job_status}"
        )


def main() -> None:
    """Entrypoint used by python -m execution."""
    app()


if __name__ == "__main__":
    main()
