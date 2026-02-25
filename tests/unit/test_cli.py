from __future__ import annotations

from pathlib import Path
import shutil

from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()


def _count_book_directories(root: Path) -> list[Path]:
    return [path for path in root.iterdir() if path.is_dir()]


def _patch_fake_ocr(monkeypatch) -> None:
    def _fake_run_ocr(*, raw_pdf: Path, ocr_pdf: Path, sidecar_text: Path, **_: object):
        shutil.copy2(raw_pdf, ocr_pdf)
        sidecar_text.write_text("recognized text", encoding="utf-8")

        class _Result:
            failed_pages: list[int] = []

        return _Result()

    monkeypatch.setattr("core.pipeline.run_ocr", _fake_run_ocr)


def test_convert_command(make_image_sequence, tmp_path: Path, monkeypatch) -> None:
    _patch_fake_ocr(monkeypatch)
    input_dir = make_image_sequence([1, 2, 3], directory_name="cli_book")
    output_root = tmp_path / "books"
    output_root.mkdir(parents=True, exist_ok=True)

    result = runner.invoke(app, ["convert", str(input_dir), "--output", str(output_root)])
    assert result.exit_code == 0
    assert "book_id:" in result.stdout

    created_books = _count_book_directories(output_root)
    assert len(created_books) == 1
    assert (created_books[0] / "out" / "book.pdf").exists()
    assert (created_books[0] / "out" / "book.txt").exists()


def test_convert_with_options(make_image_sequence, tmp_path: Path, monkeypatch) -> None:
    _patch_fake_ocr(monkeypatch)
    input_dir = make_image_sequence([1, 2, 3, 4], directory_name="cli_options_book")
    output_root = tmp_path / "books"
    output_root.mkdir(parents=True, exist_ok=True)

    result = runner.invoke(
        app,
        [
            "convert",
            str(input_dir),
            "--language",
            "eng",
            "--optimize",
            "max",
            "--front-cover",
            "2",
            "--back-cover",
            "4",
            "--output",
            str(output_root),
        ],
    )
    assert result.exit_code == 0
    created_books = _count_book_directories(output_root)
    assert len(created_books) == 1
    assert (created_books[0] / "manifest.json").exists()

