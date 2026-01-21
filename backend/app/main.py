from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.chat.memory import create_session_id, load_history, save_message
from app.core import config

from app.rag.agent import run_agent

app = FastAPI(title="Policy Chatbot API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Helpers
# -------------------------

def _to_jsonable(obj: Any) -> Any:
    """
    Converts dataclasses (and nested dataclasses) into JSON-serializable dicts.
    """
    if is_dataclass(obj):
        return _to_jsonable(asdict(obj))
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_jsonable(x) for x in obj]
    return obj


# -------------------------
# API Schemas
# -------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session id for chat history",
    )
    broad_k: int = 25
    file_k: int = 5
    final_k: int = 6


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[dict]
    retrieval: dict


# -------------------------
# Routes
# -------------------------

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> Dict[str, Any]:
    """
    Agent-driven chat endpoint.

    Flow:
    1) ensure session_id
    2) save user message
    3) load recent history
    4) run agent (agent calls tools)
    5) save assistant answer
    6) return structured payload
    """
    session_id = req.session_id or create_session_id()

    # Persisting the user query
    save_message(session_id=session_id, role="user", content=req.message)

    history = load_history(session_id=session_id, limit=12)

    try:
        agent_out = run_agent(
            user_message=req.message,
            history=history,
            session_id=session_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed: {e}")

    agent_out = _to_jsonable(agent_out)

    # Persisting the response
    try:
        save_message(
            session_id=session_id,
            role="assistant",
            content=str(agent_out.get("answer", "")),
            metadata={
                "mode": (agent_out.get("retrieval") or {}).get("mode"),
                "chosen_files": (agent_out.get("retrieval") or {}).get("chosen_files"),
            },
        )
    except Exception:
        # Will be tightened later
        pass

    return {
        "session_id": session_id,
        "answer": agent_out.get("answer", ""),
        "sources": agent_out.get("sources", []),
        "retrieval": agent_out.get("retrieval", {}),
    }
