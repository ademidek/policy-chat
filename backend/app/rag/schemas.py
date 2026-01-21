from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Literal


# -------------------------
# Core retrieval primitives
# -------------------------

@dataclass(frozen=True)
class Hit:
    """
    One retrieved chunk from ChromaDB.
    """
    text: str
    meta: Dict[str, Any]
    distance: Optional[float] = None


TwoStepMode = Literal["two_step", "one_step_fallback"]


@dataclass(frozen=True)
class TwoStepRetrievalResult:
    """
    Output of two-step retrieval:
      1) broad search across all docs
      2) choose top unique files
      3) narrow search restricted to those files
    """
    query: str
    chosen_files: List[str]
    broad_hits: List[Hit]
    narrow_hits: List[Hit]
    mode: TwoStepMode


# -------------------------
# Generation (LLM) outputs
# -------------------------

@dataclass(frozen=True)
class Source:
    """
    A compact representation of where an answer came from.
    Keep this stable for the frontend.
    """
    file_name: Optional[str]
    chunk_part: Optional[int]
    distance: Optional[float]
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class AnswerResult:
    """
    Final answer + sources ready to return from API.
    """
    answer: str
    sources: List[Source]
    retrieval: TwoStepRetrievalResult
