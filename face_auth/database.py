"""
database.py
-----------
Handles all encrypted storage of face encodings using SQLite + AES-256 (Fernet).
Face encodings are serialized with pickle, then encrypted before storage.
"""

import os
import sqlite3
import pickle
import logging
from datetime import datetime
from pathlib import Path

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "faceauth.db"
KEY_PATH = Path(__file__).parent.parent / "data" / ".key"


def _load_or_create_key() -> bytes:
    """Load the AES key from disk, or generate and save a new one."""
    if KEY_PATH.exists():
        with open(KEY_PATH, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(KEY_PATH, "wb") as f:
            f.write(key)
        # Restrict key file permissions (owner read-only)
        os.chmod(KEY_PATH, 0o600)
        logger.info("New encryption key generated and saved.")
        return key


def _get_cipher() -> Fernet:
    return Fernet(_load_or_create_key())


def init_db():
    """Initialise the SQLite database and create tables if they don't exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                encoding BLOB NOT NULL,
                enrolled_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT NOT NULL,
                user TEXT,
                success INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                details TEXT
            )
        """)
        conn.commit()
    logger.info("Database initialised at %s", DB_PATH)


def save_encoding(name: str, encoding) -> bool:
    """Encrypt and store a face encoding for a given user name."""
    cipher = _get_cipher()
    raw = pickle.dumps(encoding)
    encrypted = cipher.encrypt(raw)
    enrolled_at = datetime.utcnow().isoformat()

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO users (name, encoding, enrolled_at) VALUES (?, ?, ?)",
                (name, encrypted, enrolled_at)
            )
            conn.commit()
        logger.info("Enrolled user: %s", name)
        return True
    except sqlite3.IntegrityError:
        logger.warning("User '%s' already exists in the database.", name)
        return False


def load_all_encodings() -> list[tuple[str, any]]:
    """Load and decrypt all stored face encodings. Returns list of (name, encoding)."""
    cipher = _get_cipher()
    results = []
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT name, encoding FROM users").fetchall()
    for name, encrypted in rows:
        raw = cipher.decrypt(encrypted)
        encoding = pickle.loads(raw)
        results.append((name, encoding))
    return results


def delete_user(name: str) -> bool:
    """Remove a user and their encoding from the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("DELETE FROM users WHERE name = ?", (name,))
        conn.commit()
    if cursor.rowcount > 0:
        logger.info("Deleted user: %s", name)
        return True
    return False


def list_users() -> list[dict]:
    """Return a list of all enrolled users with metadata."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT name, enrolled_at FROM users ORDER BY enrolled_at"
        ).fetchall()
    return [{"name": r[0], "enrolled_at": r[1]} for r in rows]


def log_event(event: str, user: str = None, success: bool = True, details: str = None):
    """Write an entry to the audit log."""
    timestamp = datetime.utcnow().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO audit_log (event, user, success, timestamp, details) VALUES (?,?,?,?,?)",
            (event, user, int(success), timestamp, details)
        )
        conn.commit()


def get_audit_log(limit: int = 50) -> list[dict]:
    """Retrieve recent audit log entries."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT event, user, success, timestamp, details FROM audit_log ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [
        {"event": r[0], "user": r[1], "success": bool(r[2]), "timestamp": r[3], "details": r[4]}
        for r in rows
    ]
