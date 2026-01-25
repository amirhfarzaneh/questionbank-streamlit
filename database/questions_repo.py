from .config import get_database_url
from .db import connect

ALLOWED_DIFFICULTIES = {"easy", "medium", "hard", "unknown"}

def _is_postgres() -> bool:
    return bool(get_database_url())

def add_question(text: str, difficulty: str = "unknown") -> bool:
    text = (text or "").strip()
    difficulty = (difficulty or "unknown").strip().lower()
    if not text:
        return False

    if difficulty not in ALLOWED_DIFFICULTIES:
        difficulty = "unknown"

    if _is_postgres():
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO questions(text, difficulty) VALUES (%s, %s)",
                    (text, difficulty),
                )
            conn.commit()
        return True

    with connect() as conn:
        conn.execute(
            "INSERT INTO questions(text, difficulty) VALUES (?, ?)",
            (text, difficulty),
        )
        conn.commit()
    return True

def list_questions(limit: int = 50):
    if _is_postgres():
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, text, difficulty, created_at FROM questions ORDER BY id DESC LIMIT %s",
                    (limit,),
                )
                return cur.fetchall()

    with connect() as conn:
        return conn.execute(
            "SELECT id, text, difficulty, created_at FROM questions ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()


def delete_question(question_id: int) -> bool:
    if not question_id:
        return False

    if _is_postgres():
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM questions WHERE id = %s", (question_id,))
                deleted = cur.rowcount
            conn.commit()
        return deleted > 0

    with connect() as conn:
        cur = conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        conn.commit()
        return cur.rowcount > 0


def delete_all_questions() -> None:
    if _is_postgres():
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE questions RESTART IDENTITY")
            conn.commit()
        return

    with connect() as conn:
        conn.execute("DELETE FROM questions")
        conn.commit()