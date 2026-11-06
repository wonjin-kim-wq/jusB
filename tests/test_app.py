"""Flask 메모 API에 대한 테스트.

실제 SQLite 파일(임시 경로)을 사용한다. 메모리 DB나 목(mock)으로 대체하지 않는다.
"""
import os
import tempfile

import pytest

import db as db_module


@pytest.fixture()
def client(tmp_path):
    db_path = str(tmp_path / "test_notes.db")
    os.environ["NOTES_DB_PATH"] = db_path

    # app 모듈을 매 테스트마다 새로 import 해서 init_db가 새 경로에 대해 실행되게 한다.
    import importlib
    import app as app_module

    importlib.reload(app_module)

    app_module.app.config["TESTING"] = True

    assert os.path.exists(db_path), "실제 SQLite 파일이 생성되어야 해요"

    with app_module.app.test_client() as test_client:
        yield test_client

    if "NOTES_DB_PATH" in os.environ:
        del os.environ["NOTES_DB_PATH"]


def test_list_notes_empty(client):
    res = client.get("/api/notes")
    assert res.status_code == 200
    assert res.get_json() == {"items": []}


def test_create_note(client):
    res = client.post("/api/notes", json={"title": "첫 메모", "content": "내용입니다"})
    assert res.status_code == 201
    data = res.get_json()
    assert data["title"] == "첫 메모"
    assert data["content"] == "내용입니다"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_note_requires_title(client):
    res = client.post("/api/notes", json={"title": "", "content": "내용"})
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_TITLE"


def test_list_notes_after_create(client):
    client.post("/api/notes", json={"title": "메모1", "content": "A"})
    client.post("/api/notes", json={"title": "메모2", "content": "B"})

    res = client.get("/api/notes")
    data = res.get_json()
    assert len(data["items"]) == 2


def test_get_single_note(client):
    created = client.post("/api/notes", json={"title": "조회용", "content": "본문"}).get_json()
    res = client.get(f"/api/notes/{created['id']}")
    assert res.status_code == 200
    assert res.get_json()["title"] == "조회용"


def test_get_note_not_found(client):
    res = client.get("/api/notes/9999")
    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "NOT_FOUND"


def test_update_note(client):
    created = client.post("/api/notes", json={"title": "원래제목", "content": "원래내용"}).get_json()
    res = client.put(
        f"/api/notes/{created['id']}",
        json={"title": "수정된제목", "content": "수정된내용"},
    )
    assert res.status_code == 200
    updated = res.get_json()
    assert updated["title"] == "수정된제목"
    assert updated["content"] == "수정된내용"
    assert updated["id"] == created["id"]


def test_update_note_not_found(client):
    res = client.put("/api/notes/9999", json={"title": "x"})
    assert res.status_code == 404


def test_update_note_empty_title_rejected(client):
    created = client.post("/api/notes", json={"title": "제목", "content": "내용"}).get_json()
    res = client.put(f"/api/notes/{created['id']}", json={"title": "   "})
    assert res.status_code == 400


def test_delete_note(client):
    created = client.post("/api/notes", json={"title": "삭제할메모", "content": "내용"}).get_json()
    res = client.delete(f"/api/notes/{created['id']}")
    assert res.status_code == 200
    assert res.get_json()["deleted"] is True

    res2 = client.get(f"/api/notes/{created['id']}")
    assert res2.status_code == 404


def test_delete_note_not_found(client):
    res = client.delete("/api/notes/9999")
    assert res.status_code == 404


def test_data_persists_in_real_sqlite_file(tmp_path):
    """실제 SQLite 파일에 데이터가 저장되고, 새 연결로도 읽히는지 확인한다."""
    db_path = str(tmp_path / "persist_test.db")
    db_module.init_db(db_path)

    with db_module.db_session(db_path) as conn:
        conn.execute("INSERT INTO notes (title, content) VALUES (?, ?)", ("영속성", "테스트"))

    # 새 커넥션으로 다시 열어서 데이터가 남아있는지 확인 (메모리 DB가 아님을 증명)
    with db_module.db_session(db_path) as conn:
        row = conn.execute("SELECT * FROM notes WHERE title = ?", ("영속성",)).fetchone()
        assert row is not None
        assert row["content"] == "테스트"

    assert os.path.exists(db_path)


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"
