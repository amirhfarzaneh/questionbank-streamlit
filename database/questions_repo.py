from typing import List, Tuple
from .db import connect

def add_question(text: str) -> bool:
    text = (text or "").strip()
    if not text:
        return False

    with connect() as conn:
        conn.execute("INSERT INTO questions(text) VALUES (?)", (text,))
        conn.commit()
    return True

def list_questions(limit: int = 50) -> List[Tuple[int, str]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, text FROM questions ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return rows