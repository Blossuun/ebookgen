# ebookgen

Local tool to convert image folders into searchable PDF and TXT outputs.

## Status

- Sprint 0: bootstrap, CI, pre-commit, pytest wiring
- Sprint 1: core pipeline + `convert` CLI
- Sprint 2: SQLite state, manifest resume, worker loop, batch/status scheduling
- Sprint 3: FastAPI books/jobs API + WebSocket progress

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

Resume latest failed run for the same input:

```bash
uv run ebookgen convert ./example --resume --output ./workspace/books
```

Queue jobs from subfolders:

```bash
uv run ebookgen batch ./workspace/inbox --output ./workspace/books --queue-only
```

Run queued jobs immediately:

```bash
uv run ebookgen batch ./workspace/inbox --output ./workspace/books --run-now
```

Check status:

```bash
uv run ebookgen status --output ./workspace/books
```

Start API server:

```bash
uv run ebookgen serve --host 127.0.0.1 --port 8000
```

## API

- `GET /api/books`
- `GET /api/books/{id}`
- `POST /api/books`
- `PATCH /api/books/{id}`
- `DELETE /api/books/{id}`
- `GET /api/books/{id}/preview`
- `POST /api/jobs`
- `GET /api/jobs/{id}`
- `POST /api/jobs/{id}/cancel`
- `POST /api/jobs/{id}/retry`
- `WS /ws/jobs/{job_id}`

## Fast Dev Smoke

Create a subset instead of using the full `example/`:

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

