"""Custom exceptions for core pipeline modules."""

from __future__ import annotations


class ValidationError(Exception):
    """Base class for validation failures."""


class NoImagesError(ValidationError):
    """Raised when the input directory has no supported image files."""


class MissingPageError(ValidationError):
    """Raised when page numbers are not sequential."""

    def __init__(self, missing_pages: list[int]) -> None:
        self.missing_pages = missing_pages
        super().__init__(f"Missing pages detected: {missing_pages}")


class DuplicatePageError(ValidationError):
    """Raised when duplicate page numbers are detected."""

    def __init__(self, duplicate_pages: list[int]) -> None:
        self.duplicate_pages = duplicate_pages
        super().__init__(f"Duplicate pages detected: {duplicate_pages}")


class CorruptedImageError(ValidationError):
    """Raised when one or more image files are corrupted."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        super().__init__(f"Corrupted or unreadable image: {file_path}")


class CoverSelectionError(ValueError):
    """Raised when cover selection is invalid."""

