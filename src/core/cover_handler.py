"""Page ordering logic for front/back cover placement."""

from __future__ import annotations

from pathlib import Path

from core.errors import CoverSelectionError
from core.validator import extract_page_number


def apply_cover_order(
    page_paths: list[Path],
    front_cover: int | None = None,
    back_cover: int | None = None,
) -> list[Path]:
    """Move selected pages to front/back while preserving relative order of the rest."""
    if front_cover is None and back_cover is None:
        return list(page_paths)

    number_to_path: dict[int, Path] = {}
    for page_path in page_paths:
        page_number = extract_page_number(page_path)
        if page_number in number_to_path:
            raise CoverSelectionError(
                f"Duplicate page number {page_number} prevents unambiguous cover selection."
            )
        number_to_path[page_number] = page_path

    selected: list[Path] = []

    def _select(page_number: int | None, label: str) -> Path | None:
        if page_number is None:
            return None
        selected_path = number_to_path.get(page_number)
        if selected_path is None:
            raise CoverSelectionError(f"{label} page {page_number} is not present.")
        if selected_path in selected:
            raise CoverSelectionError("front_cover and back_cover cannot point to the same page.")
        selected.append(selected_path)
        return selected_path

    front_path = _select(front_cover, "front_cover")
    back_path = _select(back_cover, "back_cover")

    body = [path for path in page_paths if path not in selected]
    ordered: list[Path] = []
    if front_path is not None:
        ordered.append(front_path)
    ordered.extend(body)
    if back_path is not None:
        ordered.append(back_path)
    return ordered

