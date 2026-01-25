import sqlite3
from .config import get_db_path

def connect() -> sqlite3.Connection:
    # New connection per operation is fine for SQLite + Streamlit basics.
    return sqlite3.connect(get_db_path())

def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL
            )
            """
        )
        conn.commit()