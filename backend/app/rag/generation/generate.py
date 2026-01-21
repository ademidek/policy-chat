from __future__ import annotations

import os
import boto3
from typing import Any, Dict, List, Optional

from langchain_aws import ChatBedrock
from functools import lru_cache

from app.rag.generation.prompts import SYSTEM_PROMPT
from app.rag.schemas import AnswerResult, Source, TwoStepRetrievalResult


@lru_cache(maxsize=1)
def get_llm():
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
    profile = os.getenv("AWS_PROFILE")
    model_id = os.getenv("BEDROCK_MODEL_ID")

    if not model_id:
        raise RuntimeError("BEDROCK_MODEL_ID is missing. Set it in .env")

    session = (
        boto3.Session(profile_name=profile, region_name=region)
        if profile
        else boto3.Session(region_name=region)
    )
    client = session.client("bedrock-runtime")

    return ChatBedrock(
        model_id=model_id,
        client=client,
        region_name=region,
        model_kwargs={"temperature": 0.2, "max_tokens": 800},
    )


def _format_snippet(hit_text: str, max_chars: int = 900) -> str:
    """Keep context snippets reasonably small to control token usage."""
    text = (hit_text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _hit_citation(meta: Dict[str, Any]) -> str:
    """Create a stable citation token used both in context and in the final answer format."""
    file_name = meta.get("file_name", "unknown_file")
    chunk_part = meta.get("chunk_part")
    if chunk_part is None:
        return f"{file_name}"
    return f"{file_name}#{chunk_part}"


def build_context(result: TwoStepRetrievalResult, *, max_snippet_chars: int = 900) -> str:
    """
    Build the context block passed to the LLM.
    Each snippet is labeled with a citation token the model can reference.
    """
    lines: List[str] = []
    for i, hit in enumerate(result.narrow_hits, start=1):
        citation = _hit_citation(hit.meta)
        snippet = _format_snippet(hit.text, max_chars=max_snippet_chars)
        lines.append(f"[{i}] ({citation})\n{snippet}\n")
    return "\n".join(lines).strip()


def build_sources(result: TwoStepRetrievalResult) -> List[Source]:
    """Build structured sources for the frontend and API."""
    sources: List[Source] = []
    for hit in result.narrow_hits:
        meta = hit.meta or {}
        sources.append(
            Source(
                file_name=meta.get("file_name"),
                chunk_part=meta.get("chunk_part"),
                distance=hit.distance,
                metadata=meta,
            )
        )
    return sources


def _normalize_history(
    history: Optional[List[Dict[str, str]]],
    *,
    max_turns: int = 12,
) -> List[Dict[str, str]]:
    """
    Normalize chat history into a list of {"role": ..., "content": ...} dicts.
    Expects items like {"role": "user"|"assistant"|"system", "content": "..."}.

    max_turns: maximum number of history messages to include.
    """
    if not history:
        return []

    cleaned: List[Dict[str, str]] = []
    for m in history:
        if not isinstance(m, dict):
            continue
        role = (m.get("role") or "").strip().lower()
        content = (m.get("content") or "").strip()
        if not role or not content:
            continue
        if role not in {"user", "assistant", "system"}:
            continue
        cleaned.append({"role": role, "content": content})

    # Keep only the most recent N messages
    if max_turns is not None and max_turns > 0:
        cleaned = cleaned[-max_turns:]

    return cleaned


def _make_context_message(context: str) -> Dict[str, str]:
    """
    Keep retrieved snippets separated so the model doesn't confuse them with user text.
    We put it in a system message so it is treated as grounding context.
    """
    return {
        "role": "system",
        "content": (
            "Retrieved context snippets (authoritative). "
            "Use these to answer and cite sources like [file_name#chunk_part].\n\n"
            f"{context}"
        ),
    }


def generate_answer(
    llm,
    query: str,
    retrieval: TwoStepRetrievalResult,
    *,
    history: Optional[List[Dict[str, str]]] = None,
    history_max_turns: int = 12,
    max_snippet_chars: int = 900,
    extra_instructions: Optional[str] = None,
) -> AnswerResult:
    """
    Run the LLM using retrieved context + optional chat history.

    history should be a list of {"role": "user"|"assistant"|"system", "content": "..."} dicts.
    """
    context = build_context(retrieval, max_snippet_chars=max_snippet_chars)

    sys = SYSTEM_PROMPT
    if extra_instructions:
        sys = sys + "\n\n" + extra_instructions.strip()

    hist_msgs = _normalize_history(history, max_turns=history_max_turns)

    messages: List[Dict[str, str]] = [{"role": "system", "content": sys}]

    # add normalized history (user / assistant only)
    if hist_msgs:
        if hist_msgs[-1]["role"] == "user" and hist_msgs[-1]["content"].strip() == query.strip():
            hist_msgs = hist_msgs[:-1]
        messages.extend(hist_msgs)

    # put context INSIDE the user message
    user_content = (
        "Answer the question using ONLY the context below.\n"
        "If the context is insufficient, tell the user 'I'm sorry but I will need a bit more information to answer that question clearly'.\n"
        "Cite sources like [file_name#chunk_part].\n\n"
        "=== CONTEXT ===\n"
        f"{context}\n\n"
        "=== QUESTION ===\n"
        f"{query}"
    )

    messages.append({"role": "user", "content": user_content})

    resp = llm.invoke(messages)

    answer_text = getattr(resp, "content", None)
    if answer_text is None:
        answer_text = str(resp)

    sources = build_sources(retrieval)

    return AnswerResult(
        answer=answer_text.strip(),
        sources=sources,
        retrieval=retrieval,
    )
