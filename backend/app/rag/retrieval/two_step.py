from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from app.rag.chroma_client import get_chroma_collection
from app.rag.schemas import Hit, TwoStepRetrievalResult


def _normalize_query_results(results: Dict[str, Any]) -> List[Hit]:
    """
    Convert raw Chroma query output into a list of Hit dataclasses.
    Expected shape:
      {
        "documents": [[...]],
        "metadatas": [[...]],
        "distances": [[...]]
      }
    """
    documents_outer = results.get("documents") or [[]]
    metadatas_outer = results.get("metadatas") or [[]]
    distances_outer = results.get("distances") or [[]]

    documents: Sequence[str] = documents_outer[0] if documents_outer else []
    metadatas: Sequence[Dict[str, Any]] = metadatas_outer[0] if metadatas_outer else []
    distances: Sequence[Optional[float]] = distances_outer[0] if distances_outer else []

    # pad to same length
    n = len(documents)
    if len(metadatas) < n:
        metadatas = list(metadatas) + [{}] * (n - len(metadatas))
    if len(distances) < n:
        distances = list(distances) + [None] * (n - len(distances))

    hits: List[Hit] = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        hits.append(Hit(text=doc, meta=meta or {}, distance=dist))
    return hits


def _pick_top_unique_files(hits: List[Hit], file_key: str, file_k: int) -> List[str]:
    """
    Select top-N unique file names (preserving hit order) based on hit.meta[file_key].
    """
    chosen: List[str] = []
    seen = set()

    for h in hits:
        fn = h.meta.get(file_key)
        if fn and fn not in seen:
            chosen.append(fn)
            seen.add(fn)
        if len(chosen) >= file_k:
            break

    return chosen


def two_step_retrieve(
    query: str,
    broad_k: int = 25,
    file_k: int = 5,
    final_k: int = 6,
    *,
    file_key: str = "file_name",
    where_extra: Optional[Dict[str, Any]] = None,
    collection=None,
) -> TwoStepRetrievalResult:
    """
    Two-step retrieval (Broad to narrow).

    1) Perform broad semantic search across all chunks.
    2) Pick the top-N unique files from those hits.
    3) Re-query keeping the search restricted to those top-N files to get tighter chunks.

    where_extra:
      Optional additional Chroma 'where' filter merged into the narrow step.
      Example: {"policy_type": "HR"} if you store that in metadata.
    """
    if collection is None:
        collection = get_chroma_collection()

    # Step 1: Broad search
    broad_results = collection.query(
        query_texts=[query],
        n_results=broad_k,
        include=["documents", "metadatas", "distances"],
    )
    broad_hits = _normalize_query_results(broad_results)

    # Step 2: Choose top unique file names
    chosen_files = _pick_top_unique_files(broad_hits, file_key=file_key, file_k=file_k)

    # Step 3: Narrow search
    if chosen_files:
        where_clause: Dict[str, Any] = {file_key: {"$in": chosen_files}}
        if where_extra:
            # merge extra filters
            where_clause.update(where_extra)

        narrow_results = collection.query(
            query_texts=[query],
            n_results=final_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"],
        )
        narrow_hits = _normalize_query_results(narrow_results)
        mode = "two_step"
    else:
        # Fallback: if file metadata is missing, use broad hits
        narrow_hits = broad_hits[:final_k]
        mode = "one_step_fallback"

    return TwoStepRetrievalResult(
        query=query,
        chosen_files=chosen_files,
        broad_hits=broad_hits,
        narrow_hits=narrow_hits,
        mode=mode,
    )
