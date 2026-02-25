"""OCR stage implementation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
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
    error_policy: str = "abort",
    skip_big_mb: int = 50,
    timeout_sec: int = 120,
    engine: OCREngine | None = None,
) -> OCRResult:
    """Generate OCR PDF and sidecar text; fail when OCR cannot produce target artifacts."""
    ocr_pdf.parent.mkdir(parents=True, exist_ok=True)
    sidecar_text.parent.mkdir(parents=True, exist_ok=True)

    ocr_engine = engine or _load_ocr_engine()
    if ocr_engine is None:
        raise RuntimeError(
            "OCR engine is unavailable. Install ocrmypdf dependencies to generate searchable output."
        )

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
    except Exception as error:
        raise RuntimeError("OCR stage failed to produce target outputs.") from error

    if not ocr_pdf.exists() or not sidecar_text.exists():
        raise RuntimeError("OCR stage completed without required output artifacts.")

    return OCRResult(backend="ocrmypdf", failed_pages=[])

