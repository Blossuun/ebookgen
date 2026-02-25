from __future__ import annotations

import json
from pathlib import Path

from core.finalizer import finalize


def _prepare_stage(book_dir: Path) -> None:
    stage_dir = book_dir / "stage"
    stage_dir.mkdir(parents=True, exist_ok=True)
    (stage_dir / "optimized.pdf").write_bytes(b"%PDF-1.4 optimized")
    (stage_dir / "text.txt").write_text("sample text", encoding="utf-8")


def test_report_json_structure(tmp_path: Path) -> None:
    book_dir = tmp_path / "book"
    _prepare_stage(book_dir)

    result = finalize(
        book_dir=book_dir,
        title="Sample Book",
        total_pages=10,
        processing_time_sec=12.34,
        input_size_mb=5.5,
        settings={"ocr_language": "kor+eng", "optimize_mode": "basic", "error_policy": "skip"},
        covers={"front": 1, "back": 10},
        ocr_failed_pages=[3, 7],
    )

    payload = json.loads(result.report_json.read_text(encoding="utf-8"))
    assert payload["title"] == "Sample Book"
    assert payload["total_pages"] == 10
    assert payload["ocr_failed_pages"] == [3, 7]
    assert "compression_ratio" in payload
    assert "created_at" in payload


def test_output_files_exist(tmp_path: Path) -> None:
    book_dir = tmp_path / "book"
    _prepare_stage(book_dir)

    result = finalize(
        book_dir=book_dir,
        title="Sample Book",
        total_pages=2,
        processing_time_sec=1.0,
        input_size_mb=1.0,
        settings={"ocr_language": "kor+eng", "optimize_mode": "basic", "error_policy": "skip"},
        covers={"front": 1, "back": 2},
    )
    assert result.output_pdf.exists()
    assert result.output_txt.exists()
    assert result.report_json.exists()


def test_finalize_normalizes_ocr_text(tmp_path: Path) -> None:
    book_dir = tmp_path / "book"
    stage_dir = book_dir / "stage"
    stage_dir.mkdir(parents=True, exist_ok=True)
    (stage_dir / "optimized.pdf").write_bytes(b"%PDF-1.4 optimized")
    (stage_dir / "text.txt").write_text(
        "This is\nan OCR\nparagraph.\n\nhy-\nphenated words.\n",
        encoding="utf-8",
    )

    result = finalize(
        book_dir=book_dir,
        title="Sample Book",
        total_pages=2,
        processing_time_sec=1.0,
        input_size_mb=1.0,
        settings={"ocr_language": "kor+eng", "optimize_mode": "basic", "error_policy": "abort"},
        covers={"front": None, "back": None},
    )

    normalized = result.output_txt.read_text(encoding="utf-8")
    assert normalized == "This is an OCR paragraph.\n\nhyphenated words."


def test_finalize_preserves_list_and_number_lines(tmp_path: Path) -> None:
    book_dir = tmp_path / "book"
    stage_dir = book_dir / "stage"
    stage_dir.mkdir(parents=True, exist_ok=True)
    (stage_dir / "optimized.pdf").write_bytes(b"%PDF-1.4 optimized")
    (stage_dir / "text.txt").write_text(
        "1. first item\n2. second item\n\n12\nChapter title\n",
        encoding="utf-8",
    )

    result = finalize(
        book_dir=book_dir,
        title="Sample Book",
        total_pages=2,
        processing_time_sec=1.0,
        input_size_mb=1.0,
        settings={"ocr_language": "kor+eng", "optimize_mode": "basic", "error_policy": "abort"},
        covers={"front": None, "back": None},
    )

    normalized = result.output_txt.read_text(encoding="utf-8")
    assert normalized == "1. first item\n2. second item\n\n12\nChapter title"


def test_finalize_preserves_heading_and_toc_lines(tmp_path: Path) -> None:
    book_dir = tmp_path / "book"
    stage_dir = book_dir / "stage"
    stage_dir.mkdir(parents=True, exist_ok=True)
    (stage_dir / "optimized.pdf").write_bytes(b"%PDF-1.4 optimized")
    (stage_dir / "text.txt").write_text(
        (
            "Contents\n"
            "Chapter 1 .... 1\n"
            "Chapter 2 .... 17\n\n"
            "Main Title\n"
            "Subtitle\n"
            "this body line\n"
            "continues.\n"
        ),
        encoding="utf-8",
    )

    result = finalize(
        book_dir=book_dir,
        title="Sample Book",
        total_pages=2,
        processing_time_sec=1.0,
        input_size_mb=1.0,
        settings={"ocr_language": "kor+eng", "optimize_mode": "basic", "error_policy": "abort"},
        covers={"front": None, "back": None},
    )

    normalized = result.output_txt.read_text(encoding="utf-8")
    assert normalized == (
        "Contents\n"
        "Chapter 1 .... 1\n"
        "Chapter 2 .... 17\n\n"
        "Main Title\n"
        "Subtitle\n"
        "this body line continues."
    )

