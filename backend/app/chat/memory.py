from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras


def create_session_id() -> str:
    """
    Creates a new session id for a chat.
    """
    return uuid.uuid4().hex


def _get_conn():
    """
    Creates a new DB connection. For MVP this is fine.
    Later you can use a connection pool.
    """
    db_url = os.getenv("SUPABASE_DB_URL")
    if not db_url:
        raise RuntimeError("SUPABASE_DB_URL is not set in environment (.env).")
    return psycopg2.connect(db_url)


def save_message(
    session_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Persist a single chat message in Postgres (Supabase).
    """
    metadata = metadata or {}

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into chat_messages (session_id, role, content, metadata)
                values (%s, %s, %s, %s::jsonb)
                """,
                (session_id, role, content, json.dumps(metadata)),
            )
        conn.commit()


def load_history(
    session_id: str,
    limit: int = 12,
) -> List[Dict[str, str]]:
    """
    Load the most recent chat messages for a session.
    Returns messages in the format LangChain expects:
      [{"role": "user"|"assistant"|"system", "content": "..."}]
    """
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                select role, content
                from chat_messages
                where session_id = %s
                order by created_at desc
                limit %s
                """,
                (session_id, limit),
            )
            rows = cur.fetchall()

    # rows are newest-first; reverse so they're chronological
    rows = list(reversed(rows))
    return [{"role": r["role"], "content": r["content"]} for r in rows]
