from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app
from models.database import mark_job_done, mark_job_running, update_book_status


def _client(tmp_path: Path) -> TestClient:
    app = create_app(
        books_root=tmp_path / "books",
        db_path=tmp_path / "db.sqlite",
        inbox_root=tmp_path / "inbox",
        enable_watcher=False,
    )
    return TestClient(app)


def _create_book_and_job(client: TestClient, source_dir: Path) -> tuple[str, str]:
    book = client.post("/api/books", json={"path": str(source_dir)}).json()
    job = client.post("/api/jobs", json={"book_id": book["id"], "run_now": False}).json()["job"]
    return book["id"], job["id"]


def test_websocket_connects(make_image_sequence, tmp_path: Path) -> None:
    source_dir = make_image_sequence([1, 2, 3], directory_name="ws_connect")
    with _client(tmp_path) as client:
        _, job_id = _create_book_and_job(client, source_dir)
        with client.websocket_connect(f"/ws/jobs/{job_id}") as websocket:
            message = websocket.receive_json()
            assert message["type"] == "progress"
            assert message["job_id"] == job_id


def test_websocket_receives_progress(make_image_sequence, tmp_path: Path) -> None:
    source_dir = make_image_sequence([1, 2, 3], directory_name="ws_progress")
    db_path = tmp_path / "db.sqlite"
    with _client(tmp_path) as client:
        book_id, job_id = _create_book_and_job(client, source_dir)
        mark_job_running(db_path, job_id)
        update_book_status(db_path, book_id, status="running", current_stage="ocr")

        with client.websocket_connect(f"/ws/jobs/{job_id}") as websocket:
            message = websocket.receive_json()
            assert message["type"] == "progress"
            assert message["step_name"] == "ocr"
            assert message["percent"] == 60


def test_websocket_receives_completion(make_image_sequence, tmp_path: Path) -> None:
    source_dir = make_image_sequence([1, 2, 3], directory_name="ws_completion")
    db_path = tmp_path / "db.sqlite"
    with _client(tmp_path) as client:
        book_id, job_id = _create_book_and_job(client, source_dir)
        mark_job_done(db_path, job_id)
        update_book_status(db_path, book_id, status="done", current_stage="finalize")

        with client.websocket_connect(f"/ws/jobs/{job_id}") as websocket:
            first = websocket.receive_json()
            second = websocket.receive_json()
            assert first["type"] == "progress"
            assert second["type"] == "completion"
            assert second["status"] == "done"

