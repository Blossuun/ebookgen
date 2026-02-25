# 📊 ebookgen — Agile WBS + TDD

> 1주 스프린트 × 5 | 각 스프린트 끝에 **동작하는 소프트웨어** 데모 가능

---

## 개발 철학

### Agile 원칙
- **Vertical Slice**: 수평 레이어（Core→DB→API→UI）가 아니라, **기능 단위로 끝까지 관통**
- **매 스프린트 = 데모 가능한 증분**: Sprint 1부터 CLI로 PDF 생성 가능
- **YAGNI**: 필요할 때 만든다. 미리 만들지 않는다

### TDD 싸이클

```
모든 기능은 이 순서로 개발:

  🔴 RED    — 실패하는 테스트 먼저 작성
  🟢 GREEN  — 테스트를 통과하는 최소 코드
  🔵 REFACTOR — 중복 제거, 구조 개선
```

### 테스트 전략

| 레벨 | 도구 | 대상 | 실행 시점 |
|------|------|------|----------|
| Unit | pytest | core/ 모든 함수 | 매 커밋 |
| Integration | pytest + example/ | 파이프라인 E2E | 매 스프린트 |
| API | httpx + TestClient | REST + WebSocket | Phase 3~ |

---

## Sprint 0: 프로젝트 부트스트랩 (1일)

> **목표**: 개발 인프라 세팅. 코드 한 줄도 없이 테스트가 돌아가는 환경

| 작업 | 산출물 |
|------|--------|
| pyproject.toml (의존성 + pytest 설정) | `pyproject.toml` |
| src/ + tests/ 구조 생성 | 폴더 구조 |
| pytest 실행 확인 (빈 테스트) | `tests/test_smoke.py` |
| pre-commit hook (ruff + black) | `.pre-commit-config.yaml` |
| CI 스크립트 (pytest 자동 실행) | GitHub Actions or local |

```bash
# 스프린트 0 완료 기준
pytest  # → 0 passed, 0 failed
```

---

## Sprint 1: 단일 책 변환 (CLI) — 1주

> **데모**: `ebookgen convert ./example/` → `book.pdf` + `book.txt` 생성

### 🔴🟢🔵 TDD 순서

#### 1-1. Validator (2일)

```
🔴 test_validator.py
    test_detect_sequential_images()      # 연속 번호 탐지
    test_detect_missing_page()           # 누락 감지
    test_detect_duplicate_page()         # 중복 감지
    test_reject_corrupted_image()        # 손상 이미지
    test_accept_valid_directory()        # 정상 통과

🟢 validator.py — 테스트 통과하는 최소 구현
🔵 리팩터 — 에러 타입 분리 (MissingPageError, DuplicatePageError)
```

#### 1-2. Assembler + Cover Handler (1일)

```
🔴 test_assembler.py
    test_create_pdf_from_images()        # raw.pdf 생성
    test_page_count_matches_images()     # 페이지 수 일치
    test_no_image_recompression()        # 무손실 확인

🔴 test_cover_handler.py
    test_reorder_with_front_cover()      # 앞표지 재배열
    test_reorder_with_both_covers()      # 앞뒤 표지
    test_no_cover_passthrough()          # 표지 없으면 그대로

🟢 assembler.py, cover_handler.py
🔵 리팩터
```

#### 1-3. OCR + Optimizer + Finalizer (1.5일)

```
🔴 test_ocr.py
    test_ocr_creates_searchable_pdf()    # ocr.pdf 생성
    test_sidecar_text_extracted()        # text.txt 생성
    test_partial_failure_continues()     # 일부 실패 시 계속

🔴 test_optimizer.py
    test_basic_optimization()            # -O 1
    test_max_reduces_size()              # -O 3 → 용량 감소

🔴 test_finalizer.py
    test_report_json_structure()         # report.json 필드 검증
    test_output_files_exist()            # book.pdf, book.txt 존재

🟢 ocr.py, optimizer.py, finalizer.py
🔵 리팩터
```

#### 1-4. Pipeline + CLI (0.5일)

```
🔴 test_pipeline.py
    test_full_pipeline_example_book()    # example/ → 전체 파이프라인
    test_manifest_tracks_stages()        # manifest.json 단계 추적

🔴 test_cli.py
    test_convert_command()               # ebookgen convert 동작
    test_convert_with_options()          # --language, --optimize

🟢 pipeline.py, cli/main.py
🔵 리팩터
```

### Sprint 1 완료 기준

```bash
ebookgen convert ./example/ --language kor+eng --optimize basic
# → workspace/books/{id}/out/book.pdf  ✅
# → workspace/books/{id}/out/book.txt  ✅
# → workspace/books/{id}/out/report.json ✅

pytest tests/ -v
# → 20+ tests passed ✅
```

---

## Sprint 2: 상태 관리 + 재시작 — 1주

> **데모**: 변환 중 프로세스 종료 → 재시작 → 이어서 진행

### TDD 순서

#### 2-1. SQLite + 모델 (1일)

```
🔴 test_database.py
    test_create_book()
    test_update_book_status()
    test_create_job()
    test_fetch_pending_jobs()

🟢 models/database.py, schemas.py
🔵 리팩터
```

#### 2-2. manifest.json 관리 (1일)

```
🔴 test_manifest.py
    test_create_manifest()               # 초기 생성
    test_update_stage_status()           # 단계 완료 마킹
    test_read_current_stage()            # 현재 단계 읽기
    test_resume_from_manifest()          # 중간부터 재개

🟢 core/manifest.py (pipeline.py 리팩터)
🔵 리팩터
```

#### 2-3. Worker Loop (2일)

```
🔴 test_worker.py
    test_worker_picks_pending_job()      # 대기 작업 선택
    test_worker_marks_done_on_success()  # 성공 시 done
    test_worker_marks_failed_on_error()  # 실패 시 failed
    test_worker_recovers_interrupted()   # 비정상 종료 복구
    test_worker_idle_when_no_jobs()      # 작업 없으면 대기

🟢 worker/loop.py
🔵 리팩터
```

#### 2-4. 스케줄링 + 배치 (1일)

```
🔴 test_scheduler.py
    test_scheduled_job_triggers_at_time()
    test_batch_creates_multiple_jobs()

🟢 스케줄 로직 (Worker에 통합)
🔵 리팩터 — CLI에 ebookgen batch, ebookgen status 추가
```

### Sprint 2 완료 기준

```bash
ebookgen convert ./example/
# 중간에 Ctrl+C로 종료
ebookgen status
# → "Python Guide: failed (interrupted at OCR stage)"

ebookgen convert ./example/ --resume
# → OCR 단계부터 이어서 진행 ✅

pytest tests/ -v
# → 35+ tests passed ✅
```

---

## Sprint 3: Web API — 1주

> **데모**: 브라우저에서 책 목록 조회, 작업 실행, 실시간 진행률 확인

### TDD 순서

#### 3-1. FastAPI + Books API (2일)

```
🔴 test_api_books.py
    test_list_books()                    # GET /api/books
    test_get_book_detail()               # GET /api/books/{id}
    test_create_book()                   # POST /api/books
    test_update_book_settings()          # PATCH /api/books/{id}
    test_delete_book()                   # DELETE /api/books/{id}
    test_get_preview_image()             # GET /api/books/{id}/preview

🟢 api/app.py, api/routes/books.py
🔵 리팩터 — 서비스 레이어 분리
```

#### 3-2. Jobs API (1일)

```
🔴 test_api_jobs.py
    test_create_job_immediate()          # POST /api/jobs (즉시)
    test_create_job_scheduled()          # POST /api/jobs (예약)
    test_get_job_status()                # GET /api/jobs/{id}
    test_cancel_job()                    # POST /api/jobs/{id}/cancel
    test_retry_failed_job()              # POST /api/jobs/{id}/retry

🟢 api/routes/jobs.py
🔵 리팩터
```

#### 3-3. WebSocket 진행률 (2일)

```
🔴 test_ws.py
    test_websocket_connects()
    test_websocket_receives_progress()   # step, percent, ETA
    test_websocket_receives_completion()

🟢 api/routes/ws.py + pipeline 이벤트 브릿지
🔵 리팩터 — 이벤트 시스템 추상화
```

### Sprint 3 완료 기준

```bash
ebookgen serve --port 8000
# → http://localhost:8000/docs (Swagger UI)

# curl로 전체 플로우 가능:
curl -X POST localhost:8000/api/books -d '{"path": "./example"}'
curl -X POST localhost:8000/api/jobs -d '{"book_id": "abc-123"}'
curl localhost:8000/api/jobs/xyz-456  # → progress 확인

pytest tests/ -v
# → 50+ tests passed ✅
```

---

## Sprint 4: Frontend UI — 1주

> **데모**: 브라우저에서 전체 UX 동작 (Dashboard → 설정 → 실행 → 진행률 → 결과)

### 개발 순서 (UI는 API 기반 테스트)

#### 4-1. Dashboard (2일)
- 책 목록 렌더링 + 상태 뱃지
- 책 추가 (경로 입력)
- 다중 선택 + 실행 버튼

#### 4-2. 책 상세 (1.5일)
- 표지 미리보기 (앞5 + 뒤5)
- 설정 3개 (OCR 언어, 최적화, 실패 처리)
- 실행 / 예약 버튼

#### 4-3. 진행률 (1.5일)
- WebSocket 연결 + 실시간 프로그레스 바
- 5단계 상태 표시 + ETA
- 완료 시 결과 파일 다운로드 링크

#### 4-4. watchdog inbox 감시 (1일)

```
🔴 test_watcher.py
    test_new_folder_detected()           # 폴더 추가 감지
    test_folder_moved_to_books()         # inbox → books 이동
    test_db_entry_created()              # DB에 등록

🟢 services/watcher_service.py
🔵 리팩터
```

### Sprint 4 완료 기준

```bash
ebookgen serve
# 브라우저에서 http://localhost:8000
# Dashboard → 책 클릭 → 설정 → 실행 → 진행률 → 결과 다운로드 ✅

pytest tests/ -v
# → 60+ tests passed ✅
```

---

## Sprint 5: 안정화 + 배포 — 1주

> **데모**: Docker 한 방 실행, 전체 시나리오 통과

| 작업 | 일 |
|------|----|
| 테스트 커버리지 80%+ 달성 | 2일 |
| 엣지 케이스 (디스크 부족, 대용량, 빈 폴더) | 1일 |
| Docker + docker-compose | 1일 |
| README + CLI 도움말 | 0.5일 |
| 성능 벤치마크 (example/ 기준) | 0.5일 |

### Sprint 5 완료 기준

```bash
docker compose up -d
# 브라우저에서 전체 플로우 동작 ✅

pytest tests/ -v --cov=src --cov-report=term
# → coverage > 80% ✅
```

---

## 스프린트별 요약

| Sprint | 기간 | 데모 가능 결과 | 누적 테스트 |
|--------|------|---------------|------------|
| **0** | 1일 | pytest 실행됨 | 0 |
| **1** | 1주 | CLI로 PDF 변환 | 20+ |
| **2** | 1주 | 재시작·배치·스케줄 | 35+ |
| **3** | 1주 | REST API + WebSocket | 50+ |
| **4** | 1주 | 웹 UI 전체 동작 | 60+ |
| **5** | 1주 | Docker 배포 완료 | 70+ (80%+ cov) |

---

## TDD 규칙 요약

| 규칙 | 설명 |
|------|------|
| **테스트 먼저** | 프로덕션 코드보다 테스트를 먼저 작성 |
| **한 번에 하나** | 한 테스트 → 한 행위 검증 |
| **외부 의존성 모킹** | ocrmypdf, 파일시스템은 unit에서 mock |
| **example/ = 통합 테스트** | 실제 이미지로 E2E는 integration 폴더 |
| **테스트 이름 규칙** | `test_동작_조건()` — 예: `test_detect_missing_page()` |
| **커밋 전 필수** | `pytest` 통과 확인 후 커밋 |

---

## 병렬 작업 (2인 기준)

| Sprint | 담당 A | 담당 B |
|--------|--------|--------|
| **1** | Validator + Assembler (TDD) | OCR + Optimizer (TDD) |
| **2** | DB + Worker (TDD) | manifest + 스케줄 (TDD) |
| **3** | Books API + Jobs API | WebSocket + 이벤트 브릿지 |
| **4** | Dashboard + 책 상세 UI | 진행률 UI + watchdog |
| **5** | 테스트 보강 + Docker | README + 벤치마크 |
