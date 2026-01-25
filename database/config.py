import os

def get_db_path() -> str:
    # For hosting later: you can override with an env var
    return os.getenv("QUESTIONBANK_DB_PATH", "questions.db")