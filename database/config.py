import os
import streamlit as st

def get_database_url() -> str | None:
    # Prefer Streamlit Secrets (Cloud + local secrets.toml), fallback to env var
    return st.secrets.get("DATABASE_URL") or os.getenv("DATABASE_URL")

def get_db_path() -> str:
    # Still useful as a local fallback if DATABASE_URL is not set
    return os.getenv("QUESTIONBANK_DB_PATH", "questions.db")