from __future__ import annotations

from pathlib import Path

from core.optimizer import optimize_pdf


def test_basic_optimization(tmp_path: Path) -> None:
    source_pdf = tmp_path / "ocr.pdf"
    source_pdf.write_bytes(b"A" * 1024)
    output_pdf = tmp_path / "optimized.pdf"

    def _engine(input_pdf: str, output_pdf_path: str, **kwargs: object) -> None:
        Path(output_pdf_path).write_bytes(Path(input_pdf).read_bytes())

    optimized = optimize_pdf(source_pdf, output_pdf, mode="basic", engine=_engine)
    assert optimized.exists()
    assert optimized.read_bytes() == source_pdf.read_bytes()


def test_max_reduces_size(tmp_path: Path) -> None:
    source_pdf = tmp_path / "ocr.pdf"
    source_pdf.write_bytes(b"A" * 4096)
    basic_pdf = tmp_path / "basic.pdf"
    max_pdf = tmp_path / "max.pdf"

    def _engine(input_pdf: str, output_pdf_path: str, **kwargs: object) -> None:
        level = kwargs.get("optimize")
        data = Path(input_pdf).read_bytes()
        if level == 3:
            Path(output_pdf_path).write_bytes(data[: len(data) // 4])
        else:
            Path(output_pdf_path).write_bytes(data)

    optimize_pdf(source_pdf, basic_pdf, mode="basic", engine=_engine)
    optimize_pdf(source_pdf, max_pdf, mode="max", engine=_engine)
    assert max_pdf.stat().st_size < basic_pdf.stat().st_size

