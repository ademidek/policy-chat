from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.rag.tools.retrieval_tools import retrieve_policy_chunks
from app.rag.tools.generation_tools import answer_from_context


def run_agent(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    session_id: Optional[str] = None,
    *,
    broad_k: int = 25,
    file_k: int = 5,
    final_k: int = 6,
    max_snippet_chars: int = 900,
    extra_instructions: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Minimal, stable "agent" orchestrator.

    Flow:
      1) retrieve_policy_chunks(query=...)
      2) answer_from_context(query=..., retrieval=..., history=...)
    """

    # Tool 1: retrieval
    retrieval_payload = retrieve_policy_chunks.invoke(
        {
            "query": user_message,
            "broad_k": broad_k,
            "file_k": file_k,
            "final_k": final_k,
            "max_snippet_chars": max_snippet_chars,
        }
    )

    # Tool 2: generation grounded in retrieval
    answer_payload = answer_from_context.invoke(
        {
            "query": user_message,
            "retrieval": retrieval_payload,
            "history": history,
            "history_max_turns": 12,
            "max_snippet_chars": max_snippet_chars,
            "extra_instructions": extra_instructions,
        }
    )

    # Ensuring session_id is present for the API response
    if session_id and isinstance(answer_payload, dict) and "session_id" not in answer_payload:
        answer_payload["session_id"] = session_id

    return answer_payload
