from __future__ import annotations

import json
from pathlib import Path
import shutil

from core.pipeline import PipelineSettings, run_pipeline


def _patch_fake_ocr(monkeypatch) -> None:
    def _fake_run_ocr(*, raw_pdf: Path, ocr_pdf: Path, sidecar_text: Path, **_: object):
        shutil.copy2(raw_pdf, ocr_pdf)
        sidecar_text.write_text("recognized text", encoding="utf-8")

        class _Result:
            failed_pages: list[int] = []

        return _Result()

    monkeypatch.setattr("core.pipeline.run_ocr", _fake_run_ocr)


def test_full_pipeline_example_book(make_image_sequence, tmp_path: Path, monkeypatch) -> None:
    _patch_fake_ocr(monkeypatch)
    input_dir = make_image_sequence([1, 2, 3, 4], directory_name="example_book")
    workspace_dir = tmp_path / "workspace" / "books"

    result = run_pipeline(
        input_dir=input_dir,
        workspace_dir=workspace_dir,
        settings=PipelineSettings(language="kor+eng", optimize_mode="basic"),
    )
    assert result.output_pdf.exists()
    assert result.output_txt.exists()
    assert result.report_json.exists()


def test_manifest_tracks_stages(make_image_sequence, tmp_path: Path, monkeypatch) -> None:
    _patch_fake_ocr(monkeypatch)
    input_dir = make_image_sequence([1, 2, 3], directory_name="manifest_book")
    workspace_dir = tmp_path / "workspace" / "books"

    result = run_pipeline(input_dir=input_dir, workspace_dir=workspace_dir, settings=PipelineSettings())

    payload = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert payload["current_stage"] == "finalize"
    assert payload["stages"]["validate"] == "done"
    assert payload["stages"]["assemble"] == "done"
    assert payload["stages"]["ocr"] == "done"
    assert payload["stages"]["optimize"] == "done"
    assert payload["stages"]["finalize"] == "done"

