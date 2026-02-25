"""Manifest helpers for stage checkpoint and resume."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from core.pipeline_types import PipelineSettings, STAGE_NAMES


def _default_stages() -> dict[str, str]:
    return {stage: "pending" for stage in STAGE_NAMES}


def create_manifest(
    *,
    book_dir: Path,
    book_id: str,
    title: str,
    settings: PipelineSettings,
) -> Path:
    manifest_path = book_dir / "manifest.json"
    payload: dict[str, Any] = {
        "book_id": book_id,
        "title": title,
        "current_stage": "validate",
        "stages": _default_stages(),
        "settings": asdict(settings),
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def read_manifest(manifest_path: Path) -> dict[str, Any]:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def write_manifest(manifest_path: Path, payload: dict[str, Any]) -> None:
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def update_stage_status(manifest_path: Path, stage: str, status: str) -> None:
    payload = read_manifest(manifest_path)
    payload["current_stage"] = stage
    payload["stages"][stage] = status
    write_manifest(manifest_path, payload)


def read_current_stage(manifest_path: Path) -> str:
    payload = read_manifest(manifest_path)
    return str(payload["current_stage"])


def read_settings(manifest_path: Path) -> PipelineSettings:
    payload = read_manifest(manifest_path)
    settings_payload = payload.get("settings", {})
    return PipelineSettings(
        language=settings_payload.get("language", "kor+eng"),
        optimize_mode=settings_payload.get("optimize_mode", "basic"),
        error_policy=settings_payload.get("error_policy", "abort"),
        front_cover=settings_payload.get("front_cover"),
        back_cover=settings_payload.get("back_cover"),
    )


def resolve_resume_stage(manifest_path: Path) -> str:
    payload = read_manifest(manifest_path)
    stages: dict[str, str] = payload.get("stages", {})

    for stage in STAGE_NAMES:
        status = stages.get(stage, "pending")
        if status != "done":
            return stage
    return STAGE_NAMES[-1]

