import streamlit as st

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

init_db()

if "review_candidate_id" not in st.session_state:
    st.session_state["review_candidate_id"] = None

col_a, col_b = st.columns(2)
with col_a:
    pick_new = st.button("New random", key="review_pick_new_random")
with col_b:
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

    st.markdown(f"### #{qid} — {text}")

    last_reviewed_pt = pd.to_datetime(last_reviewed, utc=True, errors="coerce")
    if pd.isna(last_reviewed_pt):
        last_reviewed_display = "—"
    else:
        last_reviewed_display = last_reviewed_pt.tz_convert("America/Los_Angeles").strftime("%Y-%m-%d %H:%M")

    meta_cols = st.columns(2)
    meta_cols[0].caption(f"Times reviewed: {times_reviewed or 0}")
    meta_cols[1].caption(f"Last reviewed (PT): {last_reviewed_display}")

    if link:
        st.link_button("Open link", link)

    st.divider()
    if st.button("Reviewed", type="primary"):
        if mark_reviewed(int(qid)):
            st.success("Marked reviewed.")
            st.session_state["review_candidate_id"] = None
            st.rerun()
        else:
            st.error("Could not mark reviewed.")
