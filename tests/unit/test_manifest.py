from __future__ import annotations

from pathlib import Path

from core.manifest import (
    create_manifest,
    read_current_stage,
    read_manifest,
    resolve_resume_stage,
    update_stage_status,
)
from core.pipeline_types import PipelineSettings


def test_create_manifest(tmp_path: Path) -> None:
    book_dir = tmp_path / "book"
    book_dir.mkdir(parents=True)

    manifest_path = create_manifest(
        book_dir=book_dir,
        book_id="book-1",
        title="Test Book",
        settings=PipelineSettings(),
    )
    payload = read_manifest(manifest_path)
    assert payload["book_id"] == "book-1"
    assert payload["title"] == "Test Book"
    assert payload["stages"]["validate"] == "pending"


def test_update_stage_status(tmp_path: Path) -> None:
    book_dir = tmp_path / "book"
    book_dir.mkdir(parents=True)
    manifest_path = create_manifest(
        book_dir=book_dir,
        book_id="book-1",
        title="Test Book",
        settings=PipelineSettings(),
    )

    update_stage_status(manifest_path, "validate", "done")
    payload = read_manifest(manifest_path)
    assert payload["current_stage"] == "validate"
    assert payload["stages"]["validate"] == "done"


def test_read_current_stage(tmp_path: Path) -> None:
    book_dir = tmp_path / "book"
    book_dir.mkdir(parents=True)
    manifest_path = create_manifest(
        book_dir=book_dir,
        book_id="book-1",
        title="Test Book",
        settings=PipelineSettings(),
    )
    update_stage_status(manifest_path, "ocr", "running")
    assert read_current_stage(manifest_path) == "ocr"


def test_resume_from_manifest(tmp_path: Path) -> None:
    book_dir = tmp_path / "book"
    book_dir.mkdir(parents=True)
    manifest_path = create_manifest(
        book_dir=book_dir,
        book_id="book-1",
        title="Test Book",
        settings=PipelineSettings(),
    )
    update_stage_status(manifest_path, "validate", "done")
    update_stage_status(manifest_path, "assemble", "done")
    update_stage_status(manifest_path, "ocr", "failed")

    assert resolve_resume_stage(manifest_path) == "ocr"

