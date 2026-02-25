"""Assemble image pages into a raw PDF."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from core.cover_handler import apply_cover_order
from core.errors import NoImagesError
from core.validator import list_image_files


def _write_pdf_with_img2pdf(page_paths: list[Path], output_pdf: Path) -> bool:
    try:
        import img2pdf
    except ImportError:
        return False

    output_pdf.write_bytes(img2pdf.convert([str(path) for path in page_paths]))
    return True


def _write_pdf_with_pillow(page_paths: list[Path], output_pdf: Path) -> None:
    images: list[Image.Image] = []
    for path in page_paths:
        with Image.open(path) as source_image:
            images.append(source_image.convert("RGB"))

    first, rest = images[0], images[1:]
    first.save(output_pdf, format="PDF", save_all=True, append_images=rest)
    for image in images:
        image.close()


def assemble(
    input_dir: Path,
    stage_dir: Path,
    front_cover: int | None = None,
    back_cover: int | None = None,
) -> Path:
    """Create stage/raw.pdf from sorted image files."""
    page_paths = list_image_files(input_dir)
    if not page_paths:
        raise NoImagesError(f"No supported images found in {input_dir}")

    ordered_pages = apply_cover_order(page_paths, front_cover=front_cover, back_cover=back_cover)
    stage_dir.mkdir(parents=True, exist_ok=True)
    output_pdf = stage_dir / "raw.pdf"

    if not _write_pdf_with_img2pdf(ordered_pages, output_pdf):
        _write_pdf_with_pillow(ordered_pages, output_pdf)

    return output_pdf

