// src/usePolicyChat.js
import { useCallback, useEffect, useState } from "react";
import { clearSessionId, getSessionId, sendChatMessage, setSessionId } from "./policyTransport";

export function usePolicyChat() {
  const [sessionId, _setSessionId] = useState(() => getSessionId() || null);

  useEffect(() => {
    if (sessionId) setSessionId(sessionId);
  }, [sessionId]);

  const setSessionIdState = useCallback((id) => {
    _setSessionId(id);
    if (id) setSessionId(id);
  }, []);

  const clearSessionIdState = useCallback(() => {
    clearSessionId();
    _setSessionId(null);
  }, []);

  const sendMessage = useCallback(async (text, overrideSessionId = null) => {
    const data = await sendChatMessage(text, overrideSessionId);
    if (data?.session_id) setSessionIdState(data.session_id);
    return data;
  }, [setSessionIdState]);

  return {
    sessionId,
    setSessionId: setSessionIdState,
    clearSessionId: clearSessionIdState,
    sendMessage,
  };
}
