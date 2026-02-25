from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from core.ocr import run_ocr


def _fake_ocr_engine(input_pdf: str, output_pdf: str, **kwargs: object) -> None:
    shutil.copy2(input_pdf, output_pdf)
    sidecar = kwargs.get("sidecar")
    if isinstance(sidecar, str):
        Path(sidecar).write_text("recognized text", encoding="utf-8")


def test_ocr_creates_searchable_pdf(tmp_path: Path) -> None:
    raw_pdf = tmp_path / "raw.pdf"
    raw_pdf.write_bytes(b"%PDF-1.4 fake")
    ocr_pdf = tmp_path / "ocr.pdf"
    sidecar = tmp_path / "text.txt"

    run_ocr(raw_pdf=raw_pdf, ocr_pdf=ocr_pdf, sidecar_text=sidecar, engine=_fake_ocr_engine)
    assert ocr_pdf.exists()


def test_sidecar_text_extracted(tmp_path: Path) -> None:
    raw_pdf = tmp_path / "raw.pdf"
    raw_pdf.write_bytes(b"%PDF-1.4 fake")
    ocr_pdf = tmp_path / "ocr.pdf"
    sidecar = tmp_path / "text.txt"

    run_ocr(raw_pdf=raw_pdf, ocr_pdf=ocr_pdf, sidecar_text=sidecar, engine=_fake_ocr_engine)
    assert sidecar.read_text(encoding="utf-8") == "recognized text"


def test_failure_raises_error(tmp_path: Path) -> None:
    raw_pdf = tmp_path / "raw.pdf"
    raw_pdf.write_bytes(b"%PDF-1.4 fake")
    ocr_pdf = tmp_path / "ocr.pdf"
    sidecar = tmp_path / "text.txt"

    def _failing_engine(input_pdf: str, output_pdf: str, **kwargs: object) -> None:
        raise RuntimeError("ocr failed")

    with pytest.raises(RuntimeError):
        run_ocr(
            raw_pdf=raw_pdf,
            ocr_pdf=ocr_pdf,
            sidecar_text=sidecar,
            error_policy="abort",
            engine=_failing_engine,
        )


def test_missing_engine_raises_error(tmp_path: Path, monkeypatch) -> None:
    raw_pdf = tmp_path / "raw.pdf"
    raw_pdf.write_bytes(b"%PDF-1.4 fake")
    ocr_pdf = tmp_path / "ocr.pdf"
    sidecar = tmp_path / "text.txt"

    monkeypatch.setattr("core.ocr._load_ocr_engine", lambda: None)
    with pytest.raises(RuntimeError):
        run_ocr(raw_pdf=raw_pdf, ocr_pdf=ocr_pdf, sidecar_text=sidecar, engine=None)

