from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from langchain_core.tools import tool

from app.rag.retrieval.two_step import two_step_retrieve
from app.rag.schemas import TwoStepRetrievalResult


# -------------------------
# JSON helpers
# -------------------------

def _to_jsonable(obj: Any) -> Any:
    """
    Convert dataclasses / nested dataclasses into JSON-safe python primitives.
    Mirrors your main.py helper. :contentReference[oaicite:2]{index=2}
    """
    if is_dataclass(obj):
        return _to_jsonable(asdict(obj))
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_jsonable(x) for x in obj]
    return obj


def _shrink_hits(hits: List[Dict[str, Any]], *, max_chars: int = 900) -> List[Dict[str, Any]]:
    """
    Prevent tool outputs from exploding.
    Truncates hit text (not metadata).
    """
    shrunk: List[Dict[str, Any]] = []
    for h in hits:
        text = (h.get("text") or "").strip()
        if len(text) > max_chars:
            text = text[: max_chars - 3].rstrip() + "..."
        shrunk.append(
            {
                "text": text,
                "meta": h.get("meta") or {},
                "distance": h.get("distance"),
            }
        )
    return shrunk


# -------------------------
# Tool input schema
# -------------------------

class RetrievePolicyChunksInput(BaseModel):
    query: str = Field(..., min_length=1, description="User query to search policies for.")
    broad_k: int = Field(25, ge=1, le=100, description="Broad retrieval hits across all files.")
    file_k: int = Field(5, ge=1, le=20, description="Top unique files selected from broad hits.")
    final_k: int = Field(6, ge=1, le=30, description="Final narrow hits restricted to chosen files.")
    max_snippet_chars: int = Field(
        900, ge=100, le=3000, description="Max characters per snippet returned by the tool."
    )


# -------------------------
# Tool 1
# -------------------------

@tool("retrieve_policy_chunks", args_schema=RetrievePolicyChunksInput)
def retrieve_policy_chunks(
    query: str,
    broad_k: int = 25,
    file_k: int = 5,
    final_k: int = 6,
    max_snippet_chars: int = 900,
) -> Dict[str, Any]:
    """
    Two-step retrieval tool over policy chunks in ChromaDB.

    Returns a compact JSON object:
      - query
      - chosen_files
      - narrow_hits (truncated text)
      - mode

    NOTE: We intentionally DO NOT return full broad_hits by default to control tokens.
    """
    result: TwoStepRetrievalResult = two_step_retrieve(
        query=query,
        broad_k=broad_k,
        file_k=file_k,
        final_k=final_k,
    )

    payload = _to_jsonable(result)

    # Shrink narrow hits text to keep tool output small and stable
    payload["narrow_hits"] = _shrink_hits(payload.get("narrow_hits", []), max_chars=max_snippet_chars)

    payload.pop("broad_hits", None)

    return payload
