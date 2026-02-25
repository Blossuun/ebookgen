from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from core.errors import CorruptedImageError, DuplicatePageError, MissingPageError
from core.validator import validate


def test_detect_sequential_images(make_image_sequence) -> None:
    book_dir = make_image_sequence([1, 2, 3, 4])
    result = validate(book_dir)
    assert result.page_numbers == [1, 2, 3, 4]


def test_detect_missing_page(make_image_sequence) -> None:
    book_dir = make_image_sequence([1, 2, 4])
    with pytest.raises(MissingPageError) as error:
        validate(book_dir)
    assert error.value.missing_pages == [3]


def test_detect_duplicate_page(make_image_sequence) -> None:
    book_dir = make_image_sequence([1, 2])

    duplicate_png = book_dir / "0002.png"
    image = Image.new("RGB", (120, 160), color=(10, 10, 10))
    image.save(duplicate_png, format="PNG")
    image.close()

    with pytest.raises(DuplicatePageError) as error:
        validate(book_dir)
    assert error.value.duplicate_pages == [2]


def test_reject_corrupted_image(make_image_sequence) -> None:
    book_dir = make_image_sequence([1, 2, 3])
    broken_file = book_dir / "0002.jpg"
    broken_file.write_text("not-a-real-image", encoding="utf-8")

    with pytest.raises(CorruptedImageError):
        validate(book_dir)


def test_accept_valid_directory(make_image_sequence) -> None:
    book_dir = make_image_sequence([1, 2, 3])
    result = validate(book_dir)
    assert result.total_pages == 3
    assert isinstance(result.total_size_mb, float)
    assert all(isinstance(file_path, Path) for file_path in result.files)

