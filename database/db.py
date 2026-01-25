import sqlite3
from .config import get_database_url, get_db_path

def _is_postgres() -> bool:
    return bool(get_database_url())

def connect():
    if _is_postgres():
        import psycopg2
        return psycopg2.connect(get_database_url())
    return sqlite3.connect(get_db_path())

def init_db() -> None:
    if _is_postgres():
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS questions (
                        id SERIAL PRIMARY KEY,
                        text TEXT NOT NULL
                    )
                    """
                )
            conn.commit()
    else:
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