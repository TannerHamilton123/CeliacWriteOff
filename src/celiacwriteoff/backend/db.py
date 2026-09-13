import json
import sqlite3
import uuid
from collections.abc import Iterator
from typing import Any

from storage import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS items (
  id TEXT PRIMARY KEY,
  user_id TEXT REFERENCES users(id),
  source TEXT NOT NULL CHECK(source IN ('file','manual')),
  status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','extracted','failed','verified')),
  name TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  file_path TEXT,
  original_filename TEXT,
  mime_type TEXT,
  merchant_name TEXT,
  merchant_address TEXT,
  transaction_date TEXT,
  transaction_time TEXT,
  total_amount REAL,
  line_items_json TEXT,
  raw_extraction_json TEXT,
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  verified_at TEXT
);
"""


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns introduced after the initial CREATE TABLE for databases that predate them."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(items)")}
    if "user_id" not in columns:
        conn.execute("ALTER TABLE items ADD COLUMN user_id TEXT REFERENCES users(id)")


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)
        _migrate(conn)
        conn.commit()


def get_db() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def row_to_item(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["line_items"] = json.loads(item.pop("line_items_json") or "[]")
    item.pop("raw_extraction_json", None)
    item.pop("file_path", None)
    item.pop("mime_type", None)
    return item


def list_items(conn: sqlite3.Connection, user_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM items WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    return [row_to_item(row) for row in rows]


def get_item_row(conn: sqlite3.Connection, item_id: str, user_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM items WHERE id = ? AND user_id = ?", (item_id, user_id)
    ).fetchone()


def get_item(conn: sqlite3.Connection, item_id: str, user_id: str) -> dict[str, Any] | None:
    row = get_item_row(conn, item_id, user_id)
    return row_to_item(row) if row else None


def create_manual_item(
    conn: sqlite3.Connection,
    user_id: str,
    name: str,
    notes: str,
    merchant_name: str | None,
    merchant_address: str | None,
    transaction_date: str | None,
    transaction_time: str | None,
    total_amount: float | None,
    line_items: list[dict[str, Any]],
) -> str:
    item_id = new_item_id()
    conn.execute(
        """
        INSERT INTO items (
            id, user_id, source, status, name, notes, merchant_name, merchant_address,
            transaction_date, transaction_time, total_amount, line_items_json, verified_at
        )
        VALUES (?, ?, 'manual', 'verified', ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            item_id,
            user_id,
            name,
            notes,
            merchant_name,
            merchant_address,
            transaction_date,
            transaction_time,
            total_amount,
            json.dumps(line_items),
        ),
    )
    conn.commit()
    return item_id


def create_confirmed_file_item(
    conn: sqlite3.Connection,
    item_id: str,
    user_id: str,
    file_path: str,
    original_filename: str,
    mime_type: str,
    name: str,
    notes: str,
    merchant_name: str | None,
    merchant_address: str | None,
    transaction_date: str | None,
    transaction_time: str | None,
    total_amount: float | None,
    line_items: list[dict[str, Any]],
) -> None:
    conn.execute(
        """
        INSERT INTO items (
            id, user_id, source, status, name, notes, file_path, original_filename, mime_type,
            merchant_name, merchant_address, transaction_date, transaction_time,
            total_amount, line_items_json, verified_at
        )
        VALUES (?, ?, 'file', 'verified', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            item_id,
            user_id,
            name,
            notes,
            file_path,
            original_filename,
            mime_type,
            merchant_name,
            merchant_address,
            transaction_date,
            transaction_time,
            total_amount,
            json.dumps(line_items),
        ),
    )
    conn.commit()


def update_item(
    conn: sqlite3.Connection, item_id: str, user_id: str, updates: dict[str, Any]
) -> None:
    if not updates:
        return
    columns = []
    values: list[Any] = []
    for key, value in updates.items():
        if key == "line_items":
            columns.append("line_items_json = ?")
            values.append(json.dumps(value))
        else:
            columns.append(f"{key} = ?")
            values.append(value)
    columns.append("updated_at = datetime('now')")
    values.append(item_id)
    values.append(user_id)
    conn.execute(
        f"UPDATE items SET {', '.join(columns)} WHERE id = ? AND user_id = ?", values
    )
    conn.commit()


def delete_item(conn: sqlite3.Connection, item_id: str, user_id: str) -> None:
    conn.execute("DELETE FROM items WHERE id = ? AND user_id = ?", (item_id, user_id))
    conn.commit()


def new_item_id() -> str:
    return uuid.uuid4().hex


def coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def new_user_id() -> str:
    return uuid.uuid4().hex


def create_user(conn: sqlite3.Connection, email: str, password_hash: str) -> str:
    user_id = new_user_id()
    conn.execute(
        "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
        (user_id, email, password_hash),
    )
    conn.commit()
    return user_id


def get_user_by_email(conn: sqlite3.Connection, email: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def get_user_by_id(conn: sqlite3.Connection, user_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def create_session(
    conn: sqlite3.Connection, token: str, user_id: str, expires_at: str
) -> None:
    conn.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires_at),
    )
    conn.commit()


def get_session_user(conn: sqlite3.Connection, token: str) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT users.* FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.token = ? AND sessions.expires_at > datetime('now')
        """,
        (token,),
    ).fetchone()


def delete_session(conn: sqlite3.Connection, token: str) -> None:
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
