from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import time

from fastapi.testclient import TestClient

from api.app import create_app
from models.database import mark_job_failed


def _client(tmp_path: Path) -> TestClient:
    app = create_app(
        books_root=tmp_path / "books",
        db_path=tmp_path / "db.sqlite",
        inbox_root=tmp_path / "inbox",
        enable_watcher=False,
    )
    return TestClient(app)


def _create_book(client: TestClient, source_dir: Path) -> dict[str, object]:
    response = client.post("/api/books", json={"path": str(source_dir)})
    assert response.status_code == 201
    return response.json()


def _wait_job_status(client: TestClient, job_id: str, *, timeout_sec: float = 5.0) -> str:
    started = time.time()
    while time.time() - started <= timeout_sec:
        response = client.get(f"/api/jobs/{job_id}")
        if response.status_code == 200:
            status = response.json()["status"]
            if status in {"done", "failed", "cancelled"}:
                return status
        time.sleep(0.05)
    return "timeout"


def test_create_job_immediate(make_image_sequence, tmp_path: Path) -> None:
    source_dir = make_image_sequence([1, 2, 3], directory_name="job_immediate")
    with _client(tmp_path) as client:
        book = _create_book(client, source_dir)
        created = client.post("/api/jobs", json={"book_id": book["id"], "run_now": True})
        assert created.status_code == 201
        payload = created.json()
        assert payload["started"] is True
        final_status = _wait_job_status(client, payload["job"]["id"])
        assert final_status == "done"


def test_create_job_scheduled(make_image_sequence, tmp_path: Path) -> None:
    source_dir = make_image_sequence([1, 2, 3], directory_name="job_scheduled")
    scheduled_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    with _client(tmp_path) as client:
        book = _create_book(client, source_dir)
        created = client.post(
            "/api/jobs",
            json={"book_id": book["id"], "run_now": False, "scheduled_at": scheduled_at},
        )
        assert created.status_code == 201
        assert created.json()["job"]["status"] == "pending"
        assert created.json()["job"]["scheduled_at"] == scheduled_at


def test_get_job_status(make_image_sequence, tmp_path: Path) -> None:
    source_dir = make_image_sequence([1, 2, 3], directory_name="job_status")
    with _client(tmp_path) as client:
        book = _create_book(client, source_dir)
        created = client.post("/api/jobs", json={"book_id": book["id"], "run_now": False}).json()
        response = client.get(f"/api/jobs/{created['job']['id']}")
        assert response.status_code == 200
        assert response.json()["status"] == "pending"


def test_cancel_job(make_image_sequence, tmp_path: Path) -> None:
    source_dir = make_image_sequence([1, 2, 3], directory_name="job_cancel")
    with _client(tmp_path) as client:
        book = _create_book(client, source_dir)
        created = client.post("/api/jobs", json={"book_id": book["id"], "run_now": False}).json()
        cancelled = client.post(f"/api/jobs/{created['job']['id']}/cancel")
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "cancelled"


def test_retry_failed_job(make_image_sequence, tmp_path: Path) -> None:
    source_dir = make_image_sequence([1, 2, 3], directory_name="job_retry")
    db_path = tmp_path / "db.sqlite"
    with _client(tmp_path) as client:
        book = _create_book(client, source_dir)
        created = client.post("/api/jobs", json={"book_id": book["id"], "run_now": False}).json()
        mark_job_failed(db_path, created["job"]["id"], "forced failure")

        retried = client.post(f"/api/jobs/{created['job']['id']}/retry", json={"run_now": False})
        assert retried.status_code == 201
        payload = retried.json()
        assert payload["job"]["resume"] is True
        assert payload["job"]["status"] == "pending"


def test_download_output_file(make_image_sequence, tmp_path: Path) -> None:
    source_dir = make_image_sequence([1, 2, 3], directory_name="job_output")
    with _client(tmp_path) as client:
        book = _create_book(client, source_dir)
        created = client.post("/api/jobs", json={"book_id": book["id"], "run_now": True}).json()
        final_status = _wait_job_status(client, created["job"]["id"])
        assert final_status == "done"

        response = client.get(f"/api/output/{book['id']}/book.pdf")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

