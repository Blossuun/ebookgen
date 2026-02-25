# ebookgen

이미지 폴더를 검색 가능한 PDF(+TXT)로 변환하는 로컬 도구입니다.

## Status

- Sprint 0 완료: 프로젝트 부트스트랩, pre-commit, CI, pytest 실행 환경
- Sprint 1 완료: Core Pipeline(Validate/Assemble/OCR/Optimize/Finalize), CLI(`convert`), 테스트

## Requirements

- Python 3.11+
- `uv` (패키지/가상환경 관리)

실제 OCR(`ocrmypdf`)을 쓰려면 시스템 의존성도 필요합니다.

- Tesseract OCR (언어 데이터 포함)
- Ghostscript

## Setup

```bash
uv sync --extra dev
```

실제 OCR 엔진까지 포함하려면:

```bash
uv sync --extra dev --extra ocr
```

## Test

```bash
uv run pytest
```

## CLI

기본 사용:

```bash
uv run ebookgen convert ./example
```

개발 중 빠른 스모크 테스트(부분 샘플):

```bash
uv run python scripts/make_subset.py \
  --source ./example \
  --target ./workspace/dev-sample \
  --count 20 \
  --clean

uv run ebookgen convert ./workspace/dev-sample --output ./workspace/books
```

옵션 사용:

```bash
uv run ebookgen convert ./example \
  --language kor+eng \
  --optimize basic \
  --output ./workspace/books \
  --skip-errors
```

지원 옵션:

- `--language` OCR 언어 힌트 (기본: `kor+eng`)
- `--optimize` `basic|balanced|max`
- `--output` 결과 루트 디렉토리 (기본: `workspace/books`)
- `--skip-errors / --abort-on-error`
- `--front-cover`, `--back-cover` (페이지 번호)

## Output Layout

명령 실행 시 `workspace/books/{book_id}` 아래에 생성됩니다.

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

## Notes

- `ocrmypdf`가 없으면 Sprint 1에서는 OCR 단계를 passthrough로 처리해 산출물 생성을 유지합니다.
- 실제 검색 가능한 PDF를 원하면 `--extra ocr` 설치 및 시스템 OCR 의존성 설치가 필요합니다.

## Dev Tools

- Lint/format hooks: `pre-commit`, `ruff`, `black`
- CI: GitHub Actions (`uv sync --extra dev`, `uv run pytest`)
