from __future__ import annotations

from pathlib import Path

from core.cover_handler import apply_cover_order


def _paths() -> list[Path]:
    return [Path("0001.jpg"), Path("0002.jpg"), Path("0003.jpg"), Path("0004.jpg")]


def test_reorder_with_front_cover() -> None:
    ordered = apply_cover_order(_paths(), front_cover=3)
    assert [path.name for path in ordered] == ["0003.jpg", "0001.jpg", "0002.jpg", "0004.jpg"]


def test_reorder_with_both_covers() -> None:
    ordered = apply_cover_order(_paths(), front_cover=3, back_cover=1)
    assert [path.name for path in ordered] == ["0003.jpg", "0002.jpg", "0004.jpg", "0001.jpg"]


def test_no_cover_passthrough() -> None:
    ordered = apply_cover_order(_paths())
    assert [path.name for path in ordered] == ["0001.jpg", "0002.jpg", "0003.jpg", "0004.jpg"]

