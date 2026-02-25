"""Pydantic API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BookCreateRequest(BaseModel):
    path: str = Field(..., description="Source directory path.")
    title: str | None = None
    ocr_language: str = "kor+eng"
    optimize_mode: str = "basic"
    error_policy: str = "abort"
    front_cover: int | None = None
    back_cover: int | None = None


class BookPatchRequest(BaseModel):
    ocr_language: str | None = None
    optimize_mode: str | None = None
    error_policy: str | None = None
    front_cover: int | None = None
    back_cover: int | None = None


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    source_path: str
    book_dir: str
    status: str
    current_stage: str
    ocr_language: str
    optimize_mode: str
    error_policy: str
    front_cover: int | None
    back_cover: int | None
    created_at: str
    updated_at: str


class BookDetailResponse(BookResponse):
    manifest: dict[str, object] | None = None


class BookPreviewResponse(BaseModel):
    front: list[str]
    back: list[str]


class JobCreateRequest(BaseModel):
    book_id: str
    run_now: bool = True
    scheduled_at: str | None = None
    resume: bool = False


class JobRetryRequest(BaseModel):
    run_now: bool = True


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    book_id: str
    status: str
    scheduled_at: str | None
    started_at: str | None
    finished_at: str | None
    error_message: str | None
    resume: bool
    created_at: str
    updated_at: str


class JobCreateResponse(BaseModel):
    job: JobResponse
    started: bool = False

