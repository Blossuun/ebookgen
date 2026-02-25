"""Typer-based command-line interface for ebookgen."""

from __future__ import annotations

from pathlib import Path

import typer

from core.pipeline import PipelineSettings, run_pipeline

app = typer.Typer(
    help="Convert image folders into searchable PDF and text files.",
    no_args_is_help=True,
)


@app.callback()
def cli() -> None:
    """ebookgen command group."""


@app.command()
def convert(
    input_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    language: str = typer.Option("kor+eng", "--language", help="OCR language hint."),
    optimize: str = typer.Option("basic", "--optimize", help="basic|balanced|max"),
    output: Path = typer.Option(
        Path("workspace/books"),
        "--output",
        file_okay=False,
        dir_okay=True,
        help="Workspace root for generated book directories.",
    ),
    skip_errors: bool = typer.Option(
        True,
        "--skip-errors/--abort-on-error",
        help="Continue with fallback outputs when OCR fails.",
    ),
    front_cover: int | None = typer.Option(None, "--front-cover"),
    back_cover: int | None = typer.Option(None, "--back-cover"),
) -> None:
    """Run the full Sprint 1 conversion pipeline."""
    settings = PipelineSettings(
        language=language,
        optimize_mode=optimize,
        error_policy="skip" if skip_errors else "abort",
        front_cover=front_cover,
        back_cover=back_cover,
    )

    result = run_pipeline(
        input_dir=input_dir,
        workspace_dir=output,
        settings=settings,
    )

    typer.echo(f"book_id: {result.book_id}")
    typer.echo(f"output_dir: {result.book_dir}")
    typer.echo(f"pdf: {result.output_pdf}")
    typer.echo(f"txt: {result.output_txt}")
    typer.echo(f"report: {result.report_json}")


def main() -> None:
    """Entrypoint used by python -m execution."""
    app()


if __name__ == "__main__":
    main()
