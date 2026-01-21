from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from langchain_core.tools import tool

from app.rag.generation.generate import get_llm, generate_answer
from app.rag.schemas import Hit, TwoStepRetrievalResult


# -------------------------
# JSON helpers
# -------------------------

def _to_jsonable(obj: Any) -> Any:
    """
    Convert dataclasses / nested dataclasses into JSON-safe primitives.
    Same idea as your FastAPI helper. :contentReference[oaicite:5]{index=5}
    """
    if is_dataclass(obj):
        return _to_jsonable(asdict(obj))
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_jsonable(x) for x in obj]
    return obj


def _hits_from_payload(hits_payload: List[Dict[str, Any]]) -> List[Hit]:
    """
    Convert JSON hits like {"text":..., "meta":..., "distance":...} back into Hit dataclasses.
    """
    hits: List[Hit] = []
    for h in hits_payload or []:
        hits.append(
            Hit(
                text=(h.get("text") or ""),
                meta=(h.get("meta") or {}),
                distance=h.get("distance"),
            )
        )
    return hits


def _retrieval_from_payload(payload: Dict[str, Any]) -> TwoStepRetrievalResult:
    """
    Rebuild a TwoStepRetrievalResult from JSON output returned by Tool 1.
    Tool 1 returns narrow_hits (and may omit broad_hits). :contentReference[oaicite:6]{index=6}
    """
    return TwoStepRetrievalResult(
        query=payload.get("query") or "",
        chosen_files=list(payload.get("chosen_files") or []),
        broad_hits=_hits_from_payload(payload.get("broad_hits") or []),
        narrow_hits=_hits_from_payload(payload.get("narrow_hits") or []),
        mode=payload.get("mode") or "two_step",
    )


# -------------------------
# Tool input schema
# -------------------------

class AnswerFromContextInput(BaseModel):
    query: str = Field(..., min_length=1, description="User question.")
    retrieval: Dict[str, Any] = Field(
        ...,
        description="Retrieval payload, typically the output from retrieve_policy_chunks tool (Tool 1).",
    )
    history: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description='Optional chat history like [{"role":"user","content":"..."}, ...]',
    )
    history_max_turns: int = Field(12, ge=0, le=50)
    max_snippet_chars: int = Field(900, ge=100, le=3000)
    extra_instructions: Optional[str] = Field(
        default=None,
        description="Optional extra instructions for style, e.g. 'Answer in bullet points'.",
    )


# -------------------------
# Tool 2
# -------------------------

@tool("answer_from_context", args_schema=AnswerFromContextInput, return_direct=True)
def answer_from_context(
    query: str,
    retrieval: Dict[str, Any],
    history: Optional[List[Dict[str, str]]] = None,
    history_max_turns: int = 12,
    max_snippet_chars: int = 900,
    extra_instructions: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate an answer grounded in retrieved snippets.
    Returns JSON with:
      - answer
      - sources
      - retrieval
    """
    llm = get_llm()

    retrieval_dc = _retrieval_from_payload(retrieval)

    result = generate_answer(
        llm=llm,
        query=query,
        retrieval=retrieval_dc,
        history=history,
        history_max_turns=history_max_turns,
        max_snippet_chars=max_snippet_chars,
        extra_instructions=extra_instructions,
    )

    return _to_jsonable(result)
