const API_BASE = window.location.origin;

function getAuthToken() {
  return localStorage.getItem("auth_token");
}

async function authFetch(url, options = {}) {
  const token = getAuthToken();
  const headers = { ...options.headers };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (!headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  return fetch(url, { ...options, headers });
}

async function apiLogout() {
  const token = getAuthToken();
  if (!token) return;
  try {
    await fetch(`${API_BASE}/api/auth/logout`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    // Ignore errors on logout
  }
  localStorage.removeItem("auth_token");
  localStorage.removeItem("auth_email");
}

// ── Session API ──────────────────────────────────────────────────────────────

async function fetchSessions() {
  const response = await authFetch(`${API_BASE}/api/sessions`);
  if (!response.ok) throw new Error("Erro ao carregar sessoes");
  const data = await response.json();
  return data.sessions;
}

async function createSession() {
  const response = await authFetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  if (!response.ok) throw new Error("Erro ao criar sessao");
  return response.json();
}

async function fetchSessionMessages(sessionId) {
  const response = await authFetch(`${API_BASE}/api/sessions/${sessionId}/messages`);
  if (!response.ok) throw new Error("Erro ao carregar mensagens");
  return response.json();
}

async function deleteSession(sessionId) {
  const response = await authFetch(`${API_BASE}/api/sessions/${sessionId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Erro ao remover sessao");
}

// ── Chat API ─────────────────────────────────────────────────────────────────

async function sendMessageStream({ message, history, sessionId, onDelta, signal }) {
  const response = await authFetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    body: JSON.stringify({ message, history, session_id: sessionId }),
    signal,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body?.detail || "Erro ao enviar mensagem para o servidor.";
    throw new Error(detail);
  }

  if (!response.body) {
    throw new Error("Streaming nao suportado no ambiente atual.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const rawEvent of events) {
      const line = rawEvent
        .split("\n")
        .find((part) => part.startsWith("data:"));
      if (!line) continue;

      const payloadText = line.slice(5).trim();
      if (!payloadText) continue;

      let payload;
      try {
        payload = JSON.parse(payloadText);
      } catch {
        continue;
      }

      if (payload.error) {
        throw new Error(payload.error);
      }

      if (payload.delta) {
        onDelta(payload.delta);
      }
    }
  }
}
