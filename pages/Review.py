import streamlit as st

import random
from datetime import datetime, timezone

import pandas as pd

from database.db import connect, init_db
from database.questions_repo import get_question_by_id, get_random_question, list_questions, mark_reviewed


def check_db_connection() -> tuple[bool, str | None]:
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        _ = cur.fetchone()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


st.title("Review")

ok, err = check_db_connection()
if ok:
    st.sidebar.success("Database connection: OK")
else:
    st.sidebar.error("Database connection: FAILED")
    with st.sidebar.expander("Error details"):
        st.code(err)

st.sidebar.divider()
st.sidebar.caption("built with :heart: by Amir Hossein Farzaneh")

init_db()

if "review_candidate_id" not in st.session_state:
    st.session_state["review_candidate_id"] = None


def _due_score(last_reviewed_value, times_reviewed_value) -> float:
    """Higher means more due."""
    reviewed_count = 0
    try:
        if times_reviewed_value is not None:
            reviewed_count = int(times_reviewed_value)
    except Exception:
        reviewed_count = 0

    reviewed_count = max(0, reviewed_count)
    interval_days = 2 ** reviewed_count

    lr = pd.to_datetime(last_reviewed_value, utc=True, errors="coerce")
    if pd.isna(lr):
        days_since = 10000.0
    else:
        now = datetime.now(timezone.utc)
        days_since = max(0.0, (now - lr.to_pydatetime()).total_seconds() / 86400.0)

    return float(days_since / interval_days)


def _pick_most_due(rows):
    if not rows:
        return None, None

    scored = []
    for r in rows:
        # r: (id, text, difficulty, created_at, link, last_reviewed, times_reviewed)
        score = _due_score(r[5], r[6])
        scored.append((score, r))

    scored.sort(key=lambda x: (x[0], -(x[1][6] or 0)), reverse=True)
    best_score, best_row = scored[0]
    return best_row, best_score


def _pick_due_with_randomness(rows, *, top_k: int = 10):
    if not rows:
        return None, None

    scored = []
    for r in rows:
        score = _due_score(r[5], r[6])
        scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[: max(1, min(top_k, len(scored)))]

    weights = [max(0.0001, s) for s, _ in top]
    chosen_score, chosen_row = random.choices(top, weights=weights, k=1)[0]
    return chosen_row, chosen_score

col_a, col_b, col_c = st.columns([1, 1, 2])
with col_a:
    pick_new = st.button("New random", key="review_pick_new_random")

with col_b:
    pick_intel_1 = st.button("Intelligent Pick 1", key="review_pick_intel_1")
    pick_intel_2 = st.button("Intelligent Pick 2", key="review_pick_intel_2")

with col_c:
    with st.form("pick_by_id_form"):
        pick_id = st.number_input("Pick by ID", min_value=1, step=1, value=1)
        pick_by_id = st.form_submit_button("Load")

if pick_by_id:
    row_by_id = get_question_by_id(int(pick_id))
    if row_by_id is None:
        st.warning("ID not found.")
    else:
        st.session_state["review_candidate_id"] = int(pick_id)
        st.rerun()

if pick_intel_1 or pick_intel_2:
    all_rows = list_questions(limit=5000)
    if pick_intel_1:
        chosen, _score = _pick_most_due(all_rows)
    else:
        chosen, _score = _pick_due_with_randomness(all_rows, top_k=10)

    if chosen is None:
        st.info("No questions yet. Add one on the Home page.")
    else:
        st.session_state["review_candidate_id"] = int(chosen[0])
        st.rerun()

row = None
if not pick_new and st.session_state["review_candidate_id"] is not None:
    for r in list_questions(limit=200):
        if int(r[0]) == int(st.session_state["review_candidate_id"]):
            row = r
            break

if row is None:
    row = get_random_question()
    st.session_state["review_candidate_id"] = row[0] if row else None

if row is None:
    st.info("No questions yet. Add one on the Home page.")
else:
    qid, text, diff, created_at, link, last_reviewed, times_reviewed = row

    score = _due_score(last_reviewed, times_reviewed)

    st.markdown(f"### #{qid} — {text}")

    last_reviewed_pt = pd.to_datetime(last_reviewed, utc=True, errors="coerce")
    if pd.isna(last_reviewed_pt):
        last_reviewed_display = "—"
    else:
        last_reviewed_display = last_reviewed_pt.tz_convert("America/Los_Angeles").strftime("%Y-%m-%d %H:%M")

    meta_cols = st.columns(2)
    meta_cols[0].caption(f"Times reviewed: {times_reviewed or 0}")
    meta_cols[1].caption(f"Last reviewed (PT): {last_reviewed_display}")

    st.caption(f"Due score: {score:.2f}")

    if link:
        st.link_button("Open link", link)

    if st.button("Reviewed", type="primary"):
        if mark_reviewed(int(qid)):
            st.success("Marked reviewed.")
            st.session_state["review_candidate_id"] = None
            st.rerun()
        else:
            st.error("Could not mark reviewed.")

st.divider()
st.subheader("How picking works")
st.markdown(
    """
**New random**: picks any random question.

**Pick by ID**: loads a specific question by its numeric id.

**Intelligent Pick 1 (due score only)**: computes a due score for every question and picks the highest.

**Intelligent Pick 2 (due score + randomness)**: computes due scores, takes the top 10 most-due questions, then randomly picks one with probability weighted by due score.

**Reviewed**: increments `times_reviewed` and sets `last_reviewed` to now.

If a question has never been reviewed, we treat `days_since_last_reviewed` as a very large number so it gets prioritized.
"""
)
