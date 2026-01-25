from .config import get_database_url
from .db import connect

def _is_postgres() -> bool:
    return bool(get_database_url())

def add_question(text: str) -> bool:
    text = (text or "").strip()
    if not text:
        return False

    if _is_postgres():
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO questions(text) VALUES (%s)", (text,))
            conn.commit()
        return True

    with connect() as conn:
        conn.execute("INSERT INTO questions(text) VALUES (?)", (text,))
        conn.commit()
    return True

def list_questions(limit: int = 50):
    if _is_postgres():
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, text FROM questions ORDER BY id DESC LIMIT %s",
                    (limit,),
                )
                return cur.fetchall()

    with connect() as conn:
        return conn.execute(
            "SELECT id, text FROM questions ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()