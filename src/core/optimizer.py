"""PDF optimization stage implementation."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Protocol


class OptimizeEngine(Protocol):
    """Protocol for optimizer engine call signature."""

    def __call__(self, input_pdf: str, output_pdf: str, **kwargs: object) -> object:
        ...


OPTIMIZE_LEVELS = {
    "basic": 1,
    "balanced": 2,
    "max": 3,
}


def _load_ocr_engine() -> OptimizeEngine | None:
    try:
        import ocrmypdf
    except ImportError:
        return None
    return ocrmypdf.ocr


def optimize_pdf(
    ocr_pdf: Path,
    optimized_pdf: Path,
    mode: str = "basic",
    engine: OptimizeEngine | None = None,
) -> Path:
    """Optimize OCR PDF using ocrmypdf optimize levels; fallback to file copy."""
    level = OPTIMIZE_LEVELS.get(mode)
    if level is None:
        allowed = ", ".join(sorted(OPTIMIZE_LEVELS))
        raise ValueError(f"Unknown optimize mode '{mode}'. Allowed: {allowed}.")

    optimized_pdf.parent.mkdir(parents=True, exist_ok=True)
    optimize_engine = engine or _load_ocr_engine()

    if optimize_engine is None:
        shutil.copy2(ocr_pdf, optimized_pdf)
        return optimized_pdf

    try:
        optimize_engine(
            str(ocr_pdf),
            str(optimized_pdf),
            optimize=level,
            skip_text=True,
        )
    except Exception:
        # Keep pipeline resilient by preserving at least OCR output.
        shutil.copy2(ocr_pdf, optimized_pdf)

    return optimized_pdf

