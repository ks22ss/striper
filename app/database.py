"""SQLite database setup and operations for users and prompt history."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "striper.db"

# History limit bounds; API validates 1..HISTORY_LIMIT_MAX
HISTORY_LIMIT_DEFAULT = 50
HISTORY_LIMIT_MAX = 100


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = _get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they do not exist."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                prompt TEXT NOT NULL,
                over_engineered_score REAL NOT NULL,
                improved_prompt TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_prompt_history_user ON prompt_history(user_id)"
        )


def get_user_by_username(username: str) -> sqlite3.Row | None:
    """Fetch user by username."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cur.fetchone()


def get_user_by_email(email: str) -> sqlite3.Row | None:
    """Fetch user by email."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM users WHERE email = ?", (email,))
        return cur.fetchone()


def get_user_by_id(user_id: int) -> sqlite3.Row | None:
    """Fetch user by id."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cur.fetchone()


def create_user(username: str, email: str, password_hash: str) -> int:
    """Insert a new user. Returns user id."""
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash),
        )
        return cur.lastrowid


def add_prompt_history(
    user_id: int,
    prompt: str,
    over_engineered_score: float,
    improved_prompt: str,
) -> int:
    """Insert a prompt analysis record. Returns record id."""
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO prompt_history (user_id, prompt, over_engineered_score, improved_prompt)
               VALUES (?, ?, ?, ?)""",
            (user_id, prompt, over_engineered_score, improved_prompt),
        )
        return cur.lastrowid


def get_prompt_history(user_id: int, limit: int = HISTORY_LIMIT_DEFAULT) -> list[sqlite3.Row]:
    """Fetch prompt history for a user, most recent first."""
    with get_db() as conn:
        cur = conn.execute(
            """SELECT id, prompt, over_engineered_score, improved_prompt, created_at
               FROM prompt_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit),
        )
        return cur.fetchall()
