# ebookgen

Local tool to convert image folders into searchable PDF and TXT outputs.

## Status

- Sprint 0: bootstrap, CI, pre-commit, pytest wiring
- Sprint 1: core pipeline + CLI convert
- Sprint 2: SQLite state, manifest resume, worker loop, batch/status scheduling

## Requirements

- Python 3.11+
- `uv`

Optional for real OCR:

- Tesseract OCR
- Ghostscript
- `uv sync --extra ocr`

## Setup

```bash
uv sync --extra dev
```

## Test

```bash
uv run pytest
```

## CLI

Convert now:

```bash
uv run ebookgen convert ./example --output ./workspace/books
```

Resume latest failed run for same input:

```bash
uv run ebookgen convert ./example --resume --output ./workspace/books
```

Queue batch jobs from subfolders:

```bash
uv run ebookgen batch ./workspace/inbox --output ./workspace/books --queue-only
```

Run batch jobs immediately:

```bash
uv run ebookgen batch ./workspace/inbox --output ./workspace/books --run-now
```

Delay batch jobs:

```bash
uv run ebookgen batch ./workspace/inbox --output ./workspace/books --delay-minutes 120
```

Check status:

```bash
uv run ebookgen status --output ./workspace/books
```

## Fast Dev Smoke

Create a small subset instead of processing all `example/` pages:

```bash
uv run python scripts/make_subset.py \
  --source ./example \
  --target ./workspace/dev-sample \
  --count 20 \
  --clean

uv run ebookgen convert ./workspace/dev-sample --output ./workspace/books
```

## Output Layout

```text
workspace/books/{book_id}/
├── input/
├── stage/
│   ├── raw.pdf
│   ├── ocr.pdf
│   ├── optimized.pdf
│   └── text.txt
├── out/
│   ├── book.pdf
│   ├── book.txt
│   └── report.json
└── manifest.json
```

SQLite state DB:

```text
workspace/db.sqlite
```

