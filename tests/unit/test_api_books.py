from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app


def _client(tmp_path: Path) -> TestClient:
    app = create_app(books_root=tmp_path / "books", db_path=tmp_path / "db.sqlite")
    return TestClient(app)


def test_list_books(make_image_sequence, tmp_path: Path) -> None:
    input_dir = make_image_sequence([1, 2, 3], directory_name="book_a")
    with _client(tmp_path) as client:
        client.post("/api/books", json={"path": str(input_dir)})
        response = client.get("/api/books")
        assert response.status_code == 200
        assert len(response.json()) == 1


def test_get_book_detail(make_image_sequence, tmp_path: Path) -> None:
    input_dir = make_image_sequence([1, 2, 3], directory_name="book_detail")
    with _client(tmp_path) as client:
        created = client.post("/api/books", json={"path": str(input_dir)}).json()
        response = client.get(f"/api/books/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]


def test_create_book(make_image_sequence, tmp_path: Path) -> None:
    input_dir = make_image_sequence([1, 2, 3], directory_name="book_create")
    with _client(tmp_path) as client:
        response = client.post("/api/books", json={"path": str(input_dir), "optimize_mode": "max"})
        assert response.status_code == 201
        assert response.json()["optimize_mode"] == "max"


def test_update_book_settings(make_image_sequence, tmp_path: Path) -> None:
    input_dir = make_image_sequence([1, 2, 3], directory_name="book_patch")
    with _client(tmp_path) as client:
        created = client.post("/api/books", json={"path": str(input_dir)}).json()
        response = client.patch(
            f"/api/books/{created['id']}",
            json={"ocr_language": "eng", "optimize_mode": "balanced"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["ocr_language"] == "eng"
        assert payload["optimize_mode"] == "balanced"


def test_delete_book(make_image_sequence, tmp_path: Path) -> None:
    input_dir = make_image_sequence([1, 2, 3], directory_name="book_delete")
    with _client(tmp_path) as client:
        created = client.post("/api/books", json={"path": str(input_dir)}).json()
        deleted = client.delete(f"/api/books/{created['id']}")
        assert deleted.status_code == 204
        missing = client.get(f"/api/books/{created['id']}")
        assert missing.status_code == 404


def test_get_preview_image(make_image_sequence, tmp_path: Path) -> None:
    input_dir = make_image_sequence([1, 2, 3, 4, 5, 6, 7], directory_name="book_preview")
    with _client(tmp_path) as client:
        created = client.post("/api/books", json={"path": str(input_dir)}).json()
        response = client.get(f"/api/books/{created['id']}/preview")
        assert response.status_code == 200
        payload = response.json()
        assert payload["front"] == ["0001.jpg", "0002.jpg", "0003.jpg", "0004.jpg", "0005.jpg"]
        assert payload["back"] == ["0003.jpg", "0004.jpg", "0005.jpg", "0006.jpg", "0007.jpg"]

