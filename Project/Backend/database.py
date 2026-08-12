"""Lightweight SQLite persistence for conversation history and feedback.

No ORM is used on purpose - the schema is tiny and this keeps the project
dependency-light and easy to run inside Google Colab.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Sequence

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"


def init_db(db_path: Optional[Path] = None) -> Path:
    """Create the database file and table if they do not already exist."""
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_description TEXT NOT NULL,
                interests TEXT,
                themes TEXT,
                starter TEXT NOT NULL,
                useful INTEGER,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
    return path


@contextmanager
def get_connection(db_path: Optional[Path] = None):
    path = Path(db_path) if db_path else DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def add_history_entry(
    event_description: str,
    interests: Sequence[str],
    themes: Sequence[str],
    starter: str,
    db_path: Optional[Path] = None,
) -> int:
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO history (event_description, interests, themes, starter, useful, created_at)
            VALUES (?, ?, ?, ?, NULL, ?)
            """,
            (
                event_description,
                ",".join(interests),
                ",".join(themes),
                starter,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def update_feedback(history_id: int, useful: bool, db_path: Optional[Path] = None) -> bool:
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "UPDATE history SET useful = ? WHERE id = ?",
            (1 if useful else 0, history_id),
        )
        conn.commit()
        return cur.rowcount > 0


def get_history(limit: int = 50, db_path: Optional[Path] = None) -> List[dict]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]
