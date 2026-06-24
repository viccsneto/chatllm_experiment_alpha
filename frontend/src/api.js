const API_BASE = window.location.origin;

function getToken() {
  return localStorage.getItem("token");
}

function setToken(token) {
  localStorage.setItem("token", token);
}

function clearToken() {
  localStorage.removeItem("token");
}

function getAuthHeaders() {
  const token = getToken();
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

async function apiSignup(email, password) {
  const res = await fetch(`${API_BASE}/api/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Erro no cadastro");
  return data;
}

async function apiLogin(email, password) {
  const res = await fetch(`${API_BASE}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Erro no login");
  return data;
}

async function apiLogout() {
  await fetch(`${API_BASE}/api/logout`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  clearToken();
}

async function apiMe() {
  const res = await fetch(`${API_BASE}/api/me`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) return null;
  return data;
}

async function apiListSessions() {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) return [];
  return res.json();
}

async function apiCreateSession() {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Erro ao criar sessao");
  return res.json();
}

async function apiDeleteSession(sessionId) {
  await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
}

async function apiListMessages(sessionId) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) return [];
  return res.json();
}

async function sendMessageStream({ message, history, sessionId, onDelta, onSessionId, signal }) {
  const body = { message, history };
  if (sessionId) body.session_id = sessionId;

  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    const bodyErr = await response.json().catch(() => ({}));
    const detail = bodyErr?.detail || "Erro ao enviar mensagem para o servidor.";
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

      if (payload.session_id && onSessionId) {
        onSessionId(payload.session_id);
      }

      if (payload.delta) {
        onDelta(payload.delta);
      }
    }
  }
}
