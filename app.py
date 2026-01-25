import streamlit as st

import pandas as pd

from database.db import init_db, connect
from database.questions_repo import (
    add_question,
    delete_all_questions,
    delete_question,
    list_questions,
    update_question,
)

from integrations.leetcode import fetch_leetcode_problem_metadata, is_leetcode_problem_url


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_leetcode_metadata(url: str):
    return fetch_leetcode_problem_metadata(url)

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

ok, err = check_db_connection()
if ok:
    st.sidebar.success("Database connection: OK")
else:
    st.sidebar.error("Database connection: FAILED")
    with st.sidebar.expander("Error details"):
        st.code(err)

init_db()

st.title("LeetCode Problems")

with st.form("add_question_form", clear_on_submit=True):
    q = st.text_area(
        "Paste a LeetCode link (or type a problem)",
        key="question_input",
        height=80,
    )
    difficulty = st.selectbox(
        "Difficulty",
        ["unknown", "easy", "medium", "hard"],
        index=0,
        key="difficulty_input",
    )
    submitted = st.form_submit_button("Add")

if submitted:
    text_to_add = q
    question_id = None

    if is_leetcode_problem_url(q):
        try:
            with st.spinner("Fetching problem title from LeetCode..."):
                meta = _cached_leetcode_metadata(q)
            text_to_add = meta.title
            question_id = meta.problem_id

            if question_id is not None:
                st.info(f"Detected LeetCode problem #{question_id}: {text_to_add}")
            else:
                st.info(f"Detected LeetCode title: {text_to_add}")
        except Exception as e:
            st.warning("Could not fetch LeetCode title; saving your input as-is.")
            with st.expander("Error details"):
                st.code(str(e))

    if add_question(text_to_add, difficulty=difficulty, question_id=question_id):
        st.success("Added.")
    else:
        st.error("Please enter a non-empty question.")

st.divider()
st.subheader("Delete")
col1, col2 = st.columns(2)

with col1:
    with st.form("delete_one_form"):
        delete_id = st.number_input("Question ID", min_value=1, step=1, value=1)
        delete_one = st.form_submit_button("Delete selected ID")

    if delete_one:
        if delete_question(int(delete_id)):
            st.success(f"Deleted question {int(delete_id)}")
        else:
            st.warning("No row deleted (ID not found).")

with col2:
    with st.form("delete_all_form"):
        confirm = st.checkbox("I understand this deletes ALL questions")
        delete_all = st.form_submit_button("Delete ALL", type="primary")

    if delete_all:
        if not confirm:
            st.warning("Please confirm before deleting all questions.")
        else:
            delete_all_questions()
            st.success("Deleted all questions.")

st.subheader("Questions Library")
rows = list_questions()
table_rows = [
    {"id": qid, "problem": text, "difficulty": diff, "date_added": created_at}
    for qid, text, diff, created_at in rows
]

df = pd.DataFrame(table_rows)

if st.session_state.get("_reset_questions_editor"):
    st.session_state.pop("questions_editor", None)
    st.session_state["_reset_questions_editor"] = False

st.caption("Edit 'problem' or 'difficulty' in the table, then click Save changes.")
edited_df = st.data_editor(
    df,
    disabled=["id", "date_added"],
    hide_index=True,
    width="content",
    num_rows="fixed",
    key="questions_editor",
)

if st.button("Save changes"):
    state = st.session_state.get("questions_editor", {})
    edited_rows = state.get("edited_rows", {})

    if not edited_rows:
        st.info("No changes to save.")
    else:
        changed = 0
        for row_index, patch in edited_rows.items():
            try:
                qid = int(df.loc[int(row_index), "id"])
            except Exception:
                continue

            new_problem = patch.get("problem") if "problem" in patch else None
            if isinstance(new_problem, str):
                new_problem = new_problem.strip()

            new_difficulty = patch.get("difficulty") if "difficulty" in patch else None
            if isinstance(new_difficulty, str):
                new_difficulty = new_difficulty.strip().lower()

            ok = update_question(qid, text=new_problem, difficulty=new_difficulty)
            if ok:
                changed += 1

        if changed:
            st.success(f"Saved {changed} change(s).")
            st.session_state["_reset_questions_editor"] = True
            st.rerun()
        else:
            st.warning("No rows were updated. Check that edited values are valid.")