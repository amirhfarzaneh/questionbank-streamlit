import streamlit as st

from database.db import init_db, connect
from database.questions_repo import add_question, list_questions

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
    st.success("Database connection: OK")
else:
    st.error("Database connection: FAILED (check DATABASE_URL / Streamlit Secrets).")
    with st.expander("Error details"):
        st.code(err)

init_db()

st.title("LeetCode Problems")

q = st.text_input("Enter a question")

if st.button("Add"):
    if add_question(q):
        st.success("Added.")
    else:
        st.error("Please enter a non-empty question.")

st.subheader("Recent questions")
for qid, text in list_questions():
    st.write(f"{qid}. {text}")