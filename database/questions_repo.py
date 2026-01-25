import sqlite3

from .config import get_database_url
from .db import connect

ALLOWED_DIFFICULTIES = {"easy", "medium", "hard", "unknown"}

def _is_postgres() -> bool:
    return bool(get_database_url())

def add_question(
    text: str,
    difficulty: str = "unknown",
    *,
    question_id: int | None = None,
    link: str | None = None,
) -> bool:
    text = (text or "").strip()
    difficulty = (difficulty or "unknown").strip().lower()
    link = (link or "").strip() or None
    if not text:
        return False

    if difficulty not in ALLOWED_DIFFICULTIES:
        difficulty = "unknown"

    if question_id is not None:
        try:
            question_id = int(question_id)
        except Exception:
            question_id = None

    if question_id is not None and question_id <= 0:
        question_id = None

    if _is_postgres():
        with connect() as conn:
            with conn.cursor() as cur:
                if question_id is None:
                    cur.execute(
                        "INSERT INTO questions(text, difficulty, link) VALUES (%s, %s, %s)",
                        (text, difficulty, link),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO questions(id, text, difficulty, link)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id)
                        DO UPDATE SET text = EXCLUDED.text, difficulty = EXCLUDED.difficulty, link = EXCLUDED.link
                        """,
                        (question_id, text, difficulty, link),
                    )
                    # Ensure future inserts without explicit id don't collide with manual ids.
                    cur.execute(
                        """
                        SELECT setval(
                            pg_get_serial_sequence('questions', 'id'),
                            (SELECT COALESCE(MAX(id), 1) FROM questions)
                        )
                        """
                    )
            conn.commit()
        return True

    with connect() as conn:
        if question_id is None:
            conn.execute(
                "INSERT INTO questions(text, difficulty, link) VALUES (?, ?, ?)",
                (text, difficulty, link),
            )
        else:
            try:
                conn.execute(
                    "INSERT INTO questions(id, text, difficulty, link) VALUES (?, ?, ?, ?)",
                    (question_id, text, difficulty, link),
                )
            except sqlite3.IntegrityError:
                conn.execute(
                    "UPDATE questions SET text = ?, difficulty = ?, link = ? WHERE id = ?",
                    (text, difficulty, link, question_id),
                )
        conn.commit()
    return True

def list_questions(limit: int = 50):
    if _is_postgres():
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, text, difficulty, created_at, link, last_reviewed, times_reviewed FROM questions ORDER BY created_at DESC, id DESC LIMIT %s",
                    (limit,),
                )
                return cur.fetchall()

    with connect() as conn:
        return conn.execute(
            "SELECT id, text, difficulty, created_at, link, last_reviewed, times_reviewed FROM questions ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,),
        ).fetchall()


def get_random_question():
    """Returns one random question row or None if table is empty."""
    if _is_postgres():
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, text, difficulty, created_at, link, last_reviewed, times_reviewed
                    FROM questions
                    ORDER BY RANDOM()
                    LIMIT 1
                    """
                )
                return cur.fetchone()

    with connect() as conn:
        return conn.execute(
            """
            SELECT id, text, difficulty, created_at, link, last_reviewed, times_reviewed
            FROM questions
            ORDER BY RANDOM()
            LIMIT 1
            """
        ).fetchone()


def get_question_by_id(question_id: int):
    if not question_id:
        return None

    if _is_postgres():
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, text, difficulty, created_at, link, last_reviewed, times_reviewed
                    FROM questions
                    WHERE id = %s
                    """,
                    (question_id,),
                )
                return cur.fetchone()

    with connect() as conn:
        return conn.execute(
            """
            SELECT id, text, difficulty, created_at, link, last_reviewed, times_reviewed
            FROM questions
            WHERE id = ?
            """,
            (question_id,),
        ).fetchone()


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


def update_question(
    question_id: int,
    *,
    text: str | None = None,
    difficulty: str | None = None,
    link: str | None = None,
    last_reviewed: object | None = None,
    times_reviewed: object | None = None,
) -> bool:
    if not question_id:
        return False

    if text is not None:
        text = (text or "").strip()
        if not text:
            return False

    if difficulty is not None:
        difficulty = (difficulty or "unknown").strip().lower()
        if difficulty not in ALLOWED_DIFFICULTIES:
            difficulty = "unknown"

    if link is not None:
        link = (link or "").strip() or None

    if times_reviewed is not None:
        try:
            times_reviewed = int(times_reviewed)
        except Exception:
            return False
        if times_reviewed < 0:
            return False

    if last_reviewed is not None:
        # Allow passing datetime objects (psycopg2 handles) or strings.
        if isinstance(last_reviewed, str):
            last_reviewed = last_reviewed.strip() or None

    if text is None and difficulty is None and link is None and last_reviewed is None and times_reviewed is None:
        return False

    if _is_postgres():
        sets: list[str] = []
        params: list[object] = []
        if text is not None:
            sets.append("text = %s")
            params.append(text)
        if difficulty is not None:
            sets.append("difficulty = %s")
            params.append(difficulty)
        if link is not None:
            sets.append("link = %s")
            params.append(link)
        if last_reviewed is not None:
            sets.append("last_reviewed = %s")
            params.append(last_reviewed)
        if times_reviewed is not None:
            sets.append("times_reviewed = %s")
            params.append(times_reviewed)
        params.append(question_id)

        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE questions SET {', '.join(sets)} WHERE id = %s",
                    tuple(params),
                )
                updated = cur.rowcount
            conn.commit()
        return updated > 0

    sets_sqlite: list[str] = []
    params_sqlite: list[object] = []
    if text is not None:
        sets_sqlite.append("text = ?")
        params_sqlite.append(text)
    if difficulty is not None:
        sets_sqlite.append("difficulty = ?")
        params_sqlite.append(difficulty)
    if link is not None:
        sets_sqlite.append("link = ?")
        params_sqlite.append(link)
    if last_reviewed is not None:
        sets_sqlite.append("last_reviewed = ?")
        params_sqlite.append(last_reviewed)
    if times_reviewed is not None:
        sets_sqlite.append("times_reviewed = ?")
        params_sqlite.append(times_reviewed)
    params_sqlite.append(question_id)

    with connect() as conn:
        cur = conn.execute(
            f"UPDATE questions SET {', '.join(sets_sqlite)} WHERE id = ?",
            tuple(params_sqlite),
        )
        conn.commit()
        return cur.rowcount > 0


def mark_reviewed(question_id: int) -> bool:
    if not question_id:
        return False

    if _is_postgres():
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE questions
                    SET last_reviewed = NOW(),
                        times_reviewed = COALESCE(times_reviewed, 0) + 1
                    WHERE id = %s
                    """,
                    (question_id,),
                )
                updated = cur.rowcount
            conn.commit()
        return updated > 0

    with connect() as conn:
        cur = conn.execute(
            """
            UPDATE questions
            SET last_reviewed = CURRENT_TIMESTAMP,
                times_reviewed = COALESCE(times_reviewed, 0) + 1
            WHERE id = ?
            """,
            (question_id,),
        )
        conn.commit()
        return cur.rowcount > 0