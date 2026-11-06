"""Flask 기반 메모 웹 애플리케이션.

실제 SQLite 파일을 저장소로 사용한다 (메모리/localStorage 대체 없음).
DB 파일 경로는 환경변수 NOTES_DB_PATH 로 지정할 수 있다.
"""
import os

from flask import Flask, jsonify, render_template, request

from db import db_session, init_db

app = Flask(__name__)

# 한 번만 생성하고, 테이블이 이미 있으면 그대로 둔다 (기존 데이터 보존).
init_db()


def row_to_dict(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "content": row["content"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def error_response(code, message, status):
    return jsonify({"error": {"code": code, "message": message}}), status


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    try:
        with db_session() as conn:
            conn.execute("SELECT 1")
        return jsonify({"status": "ok"}), 200
    except Exception:
        return error_response("DB_UNAVAILABLE", "데이터베이스에 연결할 수 없어요.", 500)


@app.get("/api/notes")
def list_notes():
    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM notes ORDER BY updated_at DESC, id DESC"
        ).fetchall()
    return jsonify({"items": [row_to_dict(r) for r in rows]}), 200


@app.get("/api/notes/<int:note_id>")
def get_note(note_id):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if row is None:
        return error_response("NOT_FOUND", "메모를 찾을 수 없어요.", 404)
    return jsonify(row_to_dict(row)), 200


@app.post("/api/notes")
def create_note():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()

    if not title:
        return error_response("INVALID_TITLE", "제목을 입력해 주세요.", 400)

    with db_session() as conn:
        cursor = conn.execute(
            "INSERT INTO notes (title, content) VALUES (?, ?)",
            (title, content),
        )
        note_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()

    return jsonify(row_to_dict(row)), 201


@app.put("/api/notes/<int:note_id>")
def update_note(note_id):
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    content = data.get("content")

    if title is not None:
        title = title.strip()
        if not title:
            return error_response("INVALID_TITLE", "제목을 입력해 주세요.", 400)
    if content is not None:
        content = content.strip()

    with db_session() as conn:
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        if row is None:
            return error_response("NOT_FOUND", "메모를 찾을 수 없어요.", 404)

        new_title = title if title is not None else row["title"]
        new_content = content if content is not None else row["content"]

        conn.execute(
            """
            UPDATE notes
            SET title = ?, content = ?, updated_at = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (new_title, new_content, note_id),
        )
        updated_row = conn.execute(
            "SELECT * FROM notes WHERE id = ?", (note_id,)
        ).fetchone()

    return jsonify(row_to_dict(updated_row)), 200


@app.delete("/api/notes/<int:note_id>")
def delete_note(note_id):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        if row is None:
            return error_response("NOT_FOUND", "메모를 찾을 수 없어요.", 404)
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))

    return jsonify({"deleted": True, "id": note_id}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
