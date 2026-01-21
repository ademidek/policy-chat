// src/policyChatUI.jsx
import React, { useEffect, useRef, useState } from "react";
import { ArrowUp, Plus, Trash2 } from "lucide-react";
import { usePolicyChat } from "./usePolicyChat";

const SESSIONS_KEY = "policyChat.sessions";
const MSG_KEY = (id) => `policyChat.messages.${id}`;

function safeParse(json, fallback) {
  try {
    const v = JSON.parse(json);
    return v ?? fallback;
  } catch {
    return fallback;
  }
}

function loadSessions() {
  return safeParse(localStorage.getItem(SESSIONS_KEY), []);
}
function saveSessions(sessions) {
  localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
}
function loadMessages(sessionId) {
  if (!sessionId) return [];
  return safeParse(localStorage.getItem(MSG_KEY(sessionId)), []);
}
function saveMessages(sessionId, messages) {
  if (!sessionId) return;
  localStorage.setItem(MSG_KEY(sessionId), JSON.stringify(messages));
}

function nowIso() {
  return new Date().toISOString();
}

function makeLocalId() {
  return `local-${crypto.randomUUID()}`;
}

function formatTitle(text) {
  const t = (text || "").trim().replace(/\s+/g, " ");
  if (!t) return "New chat";
  return t.length > 36 ? `${t.slice(0, 36)}…` : t;
}

function cx(...classes) {
  return classes.filter(Boolean).join(" ");
}

function MessageBubble({ role, text, sources }) {
  const isUser = role === "user";

  return (
    <div className="w-full border-b border-white/10">
      <div className="mx-auto max-w-3xl px-4 py-8">
        <div className="flex gap-6">
          {/* Avatar */}
          <div className="flex-shrink-0">
            <div
              className={cx(
                "flex h-10 w-10 items-center justify-center rounded-full text-sm font-medium",
                isUser ? "bg-[#520913] text-white" : "border border-white/15 text-white text-bold"
              )}
            >
              {isUser ? "U" : "PC"}
            </div>
          </div>

          {/* Message Content */}
          <div className="flex-1 space-y-2 pt-1">
            <div className={cx(
              "text-base leading-7 whitespace-pre-wrap break-words rounded-2xl px-4 py-3",
              isUser ? "bg-[#520913] text-white" : "text-[#eee]"
            )}>
              {text}
            </div>

            {/* Sources */}
            {!isUser && Array.isArray(sources) && sources.length > 0 && (
              <details className="group mt-3">
                <summary className="cursor-pointer select-none text-sm text-[#b4b4b4] hover:text-[#cdcdcd] list-none">
                  <span className="inline-flex items-center gap-1">
                    <svg
                      className="h-3 w-3 transition-transform group-open:rotate-90"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    Sources ({sources.length})
                  </span>
                </summary>
                <div className="mt-2 ml-4 space-y-1 text-sm text-[#b4b4b4]">
                  {sources.slice(0, 8).map((s, i) => (
                    <div key={i} className="flex gap-2">
                      <span className="text-[#cdcdcd]">
                        {s?.file_name ?? "source"}
                        {typeof s?.chunk_part !== "undefined" ? ` #${s.chunk_part}` : ""}
                      </span>
                      {typeof s?.distance === "number" && (
                        <span className="text-xs text-white/35">dist {s.distance.toFixed(3)}</span>
                      )}
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function PolicyChatUI() {
  const { sessionId, setSessionId, clearSessionId, sendMessage } = usePolicyChat();

  const [sessions, setSessions] = useState(() => loadSessions());
  const [activeId, setActiveId] = useState(() => sessionId || null);
  const [messages, setMessages] = useState(() => (activeId ? loadMessages(activeId) : []));
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [err, setErr] = useState("");

  const bottomRef = useRef(null);

  useEffect(() => {
    if (sessionId && sessionId !== activeId) setActiveId(sessionId);
  }, [sessionId, activeId]);

  useEffect(() => {
    if (!activeId) {
      setMessages([]);
      return;
    }
    const msgs = loadMessages(activeId);
    setMessages(msgs);
  }, [activeId]);

  useEffect(() => {
    if (!activeId || messages.length === 0) return;
    saveMessages(activeId, messages);
  }, [activeId, messages]);

  useEffect(() => {
    setTimeout(() => {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  }, [messages.length]);

  function upsertSession(id, title) {
    const next = {
      id,
      title: title || "New chat",
      updatedAt: nowIso(),
    };
    const existing = loadSessions();
    const out = [next, ...existing.filter((s) => s.id !== id)];
    saveSessions(out);
    setSessions(out);
  }

  function startNewChat() {
    setErr("");
    setInput("");
    setIsSending(false);
    clearSessionId();

    const tempId = makeLocalId();
    setActiveId(tempId);
    setSessionId(tempId);
    upsertSession(tempId, "New chat");
    setMessages([]);
  }

  function deleteChat(id) {
    const next = loadSessions().filter((s) => s.id !== id);
    saveSessions(next);
    setSessions(next);
    localStorage.removeItem(MSG_KEY(id));

    if (activeId === id) {
      setActiveId(null);
      clearSessionId();
      setMessages([]);
    }
  }

  async function onSend() {
    const text = input.trim();
    if (!text || isSending) return;

    setErr("");
    setIsSending(true);
    setInput("");

    let currentId = activeId;
    if (!currentId) {
      currentId = makeLocalId();
      setActiveId(currentId);
      setSessionId(currentId);
      upsertSession(currentId, formatTitle(text));
    }

    const userMsg = { id: crypto.randomUUID(), role: "user", text };
    setMessages((prev) => {
      const updated = [...prev, userMsg];
      saveMessages(currentId, updated);
      return updated;
    });

    upsertSession(currentId, formatTitle(text));

    try {
      const sendSessionId = currentId.startsWith("local-") ? null : currentId;
      const result = await sendMessage(text, sendSessionId);
      const realId = result?.session_id || sendSessionId || currentId;

      if (currentId.startsWith("local-") && realId && realId !== currentId) {
        setMessages((prevMessages) => {
          localStorage.removeItem(MSG_KEY(currentId));
          saveMessages(realId, prevMessages);
          return prevMessages;
        });

        const updated = loadSessions().map((s) => (s.id === currentId ? { ...s, id: realId } : s));
        saveSessions(updated);
        setSessions(updated);
        setActiveId(realId);
        setSessionId(realId);
        currentId = realId;
      }

      const assistantMsg = {
        id: crypto.randomUUID(),
        role: "assistant",
        text: result?.answer || "(No answer returned)",
        sources: result?.sources || [],
      };

      setMessages((prev) => {
        const updated = [...prev, assistantMsg];
        saveMessages(currentId, updated);
        return updated;
      });
    } catch (e) {
      setErr(e?.message || String(e));
    } finally {
      setIsSending(false);
    }
  }

  const hasConversation = messages.length > 0;

  return (
    <div className="dark flex h-screen w-screen overflow-hidden bg-[#212121] text-white">
      {/* Sidebar */}
      <aside className="hidden md:flex w-64 flex-shrink-0 flex-col border-r border-white/10 bg-[#171717]">
        <div className="p-2">
          <button
            onClick={startNewChat}
            className="flex w-full items-center gap-2 rounded-lg border border-[#520913] bg-[#520913]/10 px-3 py-2.5 text-sm text-white transition-colors hover:bg-[#520913]/20"
          >
            <Plus className="h-4 w-4" />
            New chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2">
          {sessions.length === 0 ? (
            <div className="px-2 py-6 text-sm text-white/40">No chats yet</div>
          ) : (
            <div className="flex flex-col gap-0.5">
              {sessions.map((s) => (
                <div
                  key={s.id}
                  className={cx(
                    "group relative flex cursor-pointer items-center gap-2 rounded-lg px-2 py-2.5 text-sm transition-colors hover:bg-[#520913]/10",
                    s.id === activeId && "bg-[#520913]/20"
                  )}
                  onClick={() => {
                    setErr("");
                    setActiveId(s.id);
                    setSessionId(s.id);
                  }}
                >
                  <div className="flex-1 truncate text-white/90">{s.title}</div>
                  <button
                    className="rounded-md p-1 opacity-0 transition-opacity hover:bg-white/10 group-hover:opacity-100"
                    title="Delete"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteChat(s.id);
                    }}
                  >
                    <Trash2 className="h-4 w-4 text-white/60" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex min-w-0 flex-1 flex-col">
        {/* Header */}
        {hasConversation && (
          <div className="flex-shrink-0 border-b border-white/10 bg-[#212121]">
            <div className="mx-auto max-w-3xl px-4 py-4">
              <h1 className="text-2xl font-semibold text-white">Policy Chat</h1>
            </div>
          </div>
        )}

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto">
          {!hasConversation ? (
            <div className="flex h-full flex-col items-center justify-center px-4 pt-16">
              <div className="flex h-60 w-60 items-center justify-center rounded-full border-2 border-[#520913] bg-[#520913]/5 text-4xl font-bold text-white">
                Policy Chat
              </div>
              <p className="mt-4 text-xl text-white">What policies would you like to learn about?</p>
            </div>
          ) : (
            <div className="flex flex-col">
              {messages.map((m) => (
                <MessageBubble key={m.id} role={m.role} text={m.text} sources={m.sources} />
              ))}

              {isSending && (
                <div className="w-full border-b border-white/10">
                  <div className="mx-auto max-w-3xl px-4 py-8">
                    <div className="flex gap-6">
                      <div className="flex-shrink-0">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full border border-white/15 text-sm font-medium text-white">
                          C
                        </div>
                      </div>
                      <div className="flex-1 pt-1">
                        <div className="flex items-center gap-2 text-sm text-[#b4b4b4]">
                          <span className="h-2 w-2 animate-pulse rounded-full bg-white/60" />
                          Thinking…
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>
          )}

          {err && (
            <div className="px-4 pb-4">
              <div className="mx-auto max-w-3xl rounded-xl border border-red-400/20 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                {err}
              </div>
            </div>
          )}
        </div>

        {/* Composer - Fixed at Bottom */}
        <div className="flex-shrink-0 border-t border-white/10 bg-[#212121] pb-3 pt-4">
          <div className="mx-auto w-full max-w-3xl px-4">
            <div className="mx-auto flex w-full max-w-screen-md items-end rounded-3xl bg-white/5 border border-[#520913]/30 pl-2">
              <input
                type="text"
                placeholder="Message Policy Chat"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                className="h-12 flex-grow bg-transparent p-3.5 text-white outline-none placeholder:text-white/50"
                disabled={isSending}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    onSend();
                  }
                }}
              />
              <button
                onClick={onSend}
                disabled={!input.trim() || isSending}
                className="m-2 flex h-8 w-8 items-center justify-center rounded-full bg-[#520913] hover:bg-[#6b0c18] transition-colors disabled:opacity-10"
                title="Send"
              >
                <ArrowUp className="h-5 w-5 text-white" />
              </button>
            </div>
            <p className="p-2 text-center text-xs text-[#cdcdcd]">
              Policy Chat currently only has information about the University of Richmond policies.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
