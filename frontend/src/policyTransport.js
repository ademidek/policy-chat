// src/policyTransport.js
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

const SESSION_STORAGE_KEY = "policyChat.sessionId";

export function getSessionId() {
  return localStorage.getItem(SESSION_STORAGE_KEY);
}

export function setSessionId(id) {
  if (!id) return;
  localStorage.setItem(SESSION_STORAGE_KEY, id);
}

export function clearSessionId() {
  localStorage.removeItem(SESSION_STORAGE_KEY);
}

export async function sendChatMessage(message, overrideSessionId = null) {
  const session_id = overrideSessionId ?? getSessionId();

  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(
      session_id ? { session_id, message } : { message }
    ),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Backend error (${res.status}): ${text || res.statusText}`);
  }

  const data = await res.json();

  if (data?.session_id) setSessionId(data.session_id);

  return data;
}
