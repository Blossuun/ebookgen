from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from PIL import Image


@pytest.fixture()
def make_image_sequence(tmp_path: Path) -> Callable[..., Path]:
    """Create numbered JPG files under a temporary directory."""

    def _make(
        page_numbers: list[int],
        directory_name: str = "book",
        image_size: tuple[int, int] = (120, 160),
    ) -> Path:
        book_dir = tmp_path / directory_name
        book_dir.mkdir(parents=True, exist_ok=True)

        for number in page_numbers:
            page_path = book_dir / f"{number:04d}.jpg"
            image = Image.new("RGB", image_size, color=(240, 240, 240))
            image.save(page_path, format="JPEG")
            image.close()

        return book_dir

    return _make

