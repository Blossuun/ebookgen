from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from pypdf import PdfReader

from core.assembler import assemble


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_create_pdf_from_images(make_image_sequence, tmp_path: Path) -> None:
    input_dir = make_image_sequence([1, 2, 3])
    stage_dir = tmp_path / "stage"

    output_pdf = assemble(input_dir=input_dir, stage_dir=stage_dir)
    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 0


def test_page_count_matches_images(make_image_sequence, tmp_path: Path) -> None:
    input_dir = make_image_sequence([1, 2, 3, 4, 5])
    output_pdf = assemble(input_dir=input_dir, stage_dir=tmp_path / "stage")
    reader = PdfReader(str(output_pdf))
    assert len(reader.pages) == 5


def test_no_image_recompression(make_image_sequence, tmp_path: Path) -> None:
    input_dir = make_image_sequence([1, 2, 3])
    before_hashes = {path.name: _sha256(path) for path in sorted(input_dir.glob("*.jpg"))}

    assemble(input_dir=input_dir, stage_dir=tmp_path / "stage")

    after_hashes = {path.name: _sha256(path) for path in sorted(input_dir.glob("*.jpg"))}
    assert after_hashes == before_hashes

