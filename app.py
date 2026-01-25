import streamlit as st

from database.db import init_db, connect
from database.questions_repo import add_question, delete_all_questions, delete_question, list_questions

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
    q = st.text_input("Enter a question", key="question_input")
    difficulty = st.selectbox(
        "Difficulty",
        ["unknown", "easy", "medium", "hard"],
        index=0,
        key="difficulty_input",
    )
    submitted = st.form_submit_button("Add")

if submitted:
    if add_question(q, difficulty=difficulty):
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
st.dataframe(
    table_rows,
    width="content",
    hide_index=True,
)