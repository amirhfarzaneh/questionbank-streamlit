import streamlit as st

from database.db import init_db
from database.questions_repo import add_question, list_questions

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