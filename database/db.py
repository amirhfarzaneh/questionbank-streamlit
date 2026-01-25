import sqlite3
from .config import get_database_url, get_db_path

def _is_postgres() -> bool:
    return bool(get_database_url())

def connect():
    if _is_postgres():
        import psycopg2
        return psycopg2.connect(get_database_url())
    return sqlite3.connect(get_db_path())


def _sqlite_has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table});").fetchall()
    return any(r[1] == column for r in rows)

def init_db() -> None:
    if _is_postgres():
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS questions (
                        id SERIAL PRIMARY KEY,
                        text TEXT NOT NULL,
                        difficulty TEXT NOT NULL DEFAULT 'unknown'
                        ,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        ,last_reviewed TIMESTAMPTZ
                        ,times_reviewed INTEGER NOT NULL DEFAULT 0
                        ,link TEXT
                    )
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE questions
                    ADD COLUMN IF NOT EXISTS difficulty TEXT NOT NULL DEFAULT 'unknown'
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE questions
                    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE questions
                    ADD COLUMN IF NOT EXISTS link TEXT
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE questions
                    ADD COLUMN IF NOT EXISTS last_reviewed TIMESTAMPTZ
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE questions
                    ADD COLUMN IF NOT EXISTS times_reviewed INTEGER NOT NULL DEFAULT 0
                    """
                )
                cur.execute(
                    """
                    UPDATE questions
                    SET difficulty = 'unknown'
                    WHERE difficulty IS NULL
                    """
                )
                cur.execute(
                    """
                    UPDATE questions
                    SET times_reviewed = 0
                    WHERE times_reviewed IS NULL
                    """
                )
            conn.commit()
    else:
        with connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    difficulty TEXT NOT NULL DEFAULT 'unknown'
                    ,created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
                    ,last_reviewed TEXT
                    ,times_reviewed INTEGER NOT NULL DEFAULT 0
                    ,link TEXT
                )
                """
            )
            if not _sqlite_has_column(conn, "questions", "difficulty"):
                conn.execute(
                    "ALTER TABLE questions ADD COLUMN difficulty TEXT NOT NULL DEFAULT 'unknown'"
                )
            if not _sqlite_has_column(conn, "questions", "created_at"):
                conn.execute(
                    "ALTER TABLE questions ADD COLUMN created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)"
                )
            if not _sqlite_has_column(conn, "questions", "link"):
                conn.execute(
                    "ALTER TABLE questions ADD COLUMN link TEXT"
                )
            if not _sqlite_has_column(conn, "questions", "last_reviewed"):
                conn.execute(
                    "ALTER TABLE questions ADD COLUMN last_reviewed TEXT"
                )
            if not _sqlite_has_column(conn, "questions", "times_reviewed"):
                conn.execute(
                    "ALTER TABLE questions ADD COLUMN times_reviewed INTEGER NOT NULL DEFAULT 0"
                )
            conn.execute(
                "UPDATE questions SET times_reviewed = 0 WHERE times_reviewed IS NULL"
            )
            conn.commit()