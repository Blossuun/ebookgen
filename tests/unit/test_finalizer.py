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

