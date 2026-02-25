"""Shared dataclasses/constants for pipeline and manifest modules."""

from __future__ import annotations

from dataclasses import dataclass

STAGE_NAMES = ("validate", "assemble", "ocr", "optimize", "finalize")


@dataclass(frozen=True)
class PipelineSettings:
    """User-facing conversion settings."""

    language: str = "kor+eng"
    optimize_mode: str = "basic"
    error_policy: str = "abort"
    front_cover: int | None = None
    back_cover: int | None = None

