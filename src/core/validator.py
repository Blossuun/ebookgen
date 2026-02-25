"""Input validation for image-based book conversion."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re

from PIL import Image, UnidentifiedImageError

from core.errors import CorruptedImageError, DuplicatePageError, MissingPageError, NoImagesError

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
_NUMERIC_PREFIX_PATTERN = re.compile(r"^(\d+)")


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of directory validation."""

    files: list[Path]
    page_numbers: list[int]
    total_pages: int
    total_size_mb: float


def extract_page_number(path: Path) -> int:
    """Extract the numeric prefix from a filename stem."""
    match = _NUMERIC_PREFIX_PATTERN.match(path.stem)
    if not match:
        raise ValueError(f"File has no numeric prefix: {path.name}")
    return int(match.group(1))


def list_image_files(input_dir: Path) -> list[Path]:
    """Return supported image files sorted by numeric page and then name."""
    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    files = [
        file_path
        for file_path in input_dir.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    ]
    files.sort(key=lambda path: (extract_page_number(path), path.name))
    return files


def _find_missing_pages(page_numbers: list[int]) -> list[int]:
    if not page_numbers:
        return []
    expected = set(range(min(page_numbers), max(page_numbers) + 1))
    return sorted(expected.difference(page_numbers))


def _find_duplicate_pages(page_numbers: list[int]) -> list[int]:
    counts = Counter(page_numbers)
    return sorted(number for number, count in counts.items() if count > 1)


def _verify_images(files: list[Path]) -> None:
    for file_path in files:
        try:
            with Image.open(file_path) as image:
                image.verify()
        except (UnidentifiedImageError, OSError) as error:
            raise CorruptedImageError(str(file_path)) from error


def validate(input_dir: Path) -> ValidationResult:
    """Validate image sequence integrity and readability."""
    files = list_image_files(input_dir)
    if not files:
        raise NoImagesError(f"No supported images found in {input_dir}")

    page_numbers = [extract_page_number(file_path) for file_path in files]
    duplicates = _find_duplicate_pages(page_numbers)
    if duplicates:
        raise DuplicatePageError(duplicates)

    missing = _find_missing_pages(page_numbers)
    if missing:
        raise MissingPageError(missing)

    _verify_images(files)

    total_size_mb = sum(file_path.stat().st_size for file_path in files) / (1024 * 1024)
    return ValidationResult(
        files=files,
        page_numbers=page_numbers,
        total_pages=len(files),
        total_size_mb=total_size_mb,
    )
