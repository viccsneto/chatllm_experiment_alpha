const API_BASE = window.location.origin;

function getToken() {
  return localStorage.getItem("chatllm_token");
}

function authHeaders() {
  const token = getToken();
  return token ? { "Authorization": `Bearer ${token}` } : {};
}

async function apiPost(path, body) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Erro na requisicao.");
  }
  return data;
}

async function apiGet(path) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { ...authHeaders() },
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Erro na requisicao.");
  }
  return data;
}

async function register(email, password) {
  return apiPost("/api/register", { email, password });
}

async function login(email, password) {
  return apiPost("/api/login", { email, password });
}

async function logout() {
  return apiPost("/api/logout", {});
}

async function me() {
  return apiGet("/api/me");
}

// ── Session API ──
async function getSessions() {
  return apiGet("/api/sessions");
}

async function createSession(title = "") {
  return apiPost("/api/sessions", { title });
}

async function deleteSession(sessionId) {
  const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
    method: "DELETE",
    headers: { ...authHeaders() },
  });
  if (!response.ok && response.status !== 204) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Erro ao deletar sessao.");
  }
}

async function getSessionMessages(sessionId) {
  return apiGet(`/api/sessions/${sessionId}/messages`);
}

// ── Chat API ──

async function sendMessageStream({ message, sessionId, history, onDelta, signal }) {
  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ message, session_id: sessionId, history }),
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
