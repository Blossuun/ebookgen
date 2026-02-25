"""OCR stage implementation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import shutil
from typing import Protocol


class OCREngine(Protocol):
    """Protocol for OCR engine call signature."""

    def __call__(self, input_pdf: str, output_pdf: str, **kwargs: object) -> object:
        ...


@dataclass(frozen=True)
class OCRResult:
    """Metadata about OCR execution."""

    backend: str
    failed_pages: list[int]


def _load_ocr_engine() -> OCREngine | None:
    try:
        import ocrmypdf
    except ImportError:
        return None
    return ocrmypdf.ocr


def run_ocr(
    raw_pdf: Path,
    ocr_pdf: Path,
    sidecar_text: Path,
    language: str = "kor+eng",
    error_policy: str = "skip",
    skip_big_mb: int = 50,
    timeout_sec: int = 120,
    engine: OCREngine | None = None,
) -> OCRResult:
    """Generate OCR PDF and sidecar text; fallback to passthrough when engine is unavailable."""
    ocr_pdf.parent.mkdir(parents=True, exist_ok=True)
    sidecar_text.parent.mkdir(parents=True, exist_ok=True)

    ocr_engine = engine or _load_ocr_engine()
    if ocr_engine is None:
        shutil.copy2(raw_pdf, ocr_pdf)
        sidecar_text.write_text("", encoding="utf-8")
        return OCRResult(backend="passthrough", failed_pages=[])

    try:
        ocr_engine(
            str(raw_pdf),
            str(ocr_pdf),
            language=language,
            sidecar=str(sidecar_text),
            skip_big=skip_big_mb,
            tesseract_timeout=timeout_sec,
            jobs=max(1, os.cpu_count() or 1),
            deskew=True,
            rotate_pages=True,
        )
        return OCRResult(backend="ocrmypdf", failed_pages=[])
    except Exception:
        if error_policy != "skip":
            raise

        # Skip policy guarantees output artifacts are still generated.
        shutil.copy2(raw_pdf, ocr_pdf)
        sidecar_text.write_text("", encoding="utf-8")
        return OCRResult(backend="passthrough-error", failed_pages=[])

