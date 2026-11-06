"""SQLite 연결 및 스키마 관리 모듈.

DB 파일 경로는 환경변수 NOTES_DB_PATH 로 지정한다.
지정하지 않으면 기본값으로 data/notes.db 를 사용한다 (저장소 루트 기준 상대경로).
"""
import os
import sqlite3
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "notes.db")


def get_db_path():
    """환경변수 NOTES_DB_PATH 가 있으면 그 경로를, 없으면 기본 경로를 반환한다."""
    return os.environ.get("NOTES_DB_PATH", DEFAULT_DB_PATH)


def get_connection(db_path=None):
    path = db_path or get_db_path()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session(db_path=None):
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path=None):
    """테이블이 없을 때만 생성한다. 기존 데이터는 절대 삭제하지 않는다."""
    with db_session(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
