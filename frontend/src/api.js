const API_BASE = window.location.origin;

async function sendMessageStream({ message, history, sessionKey, onDelta, signal, onTitleUpdate }) {
  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history, session_key: sessionKey }),
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

      if (payload.done && payload.title && onTitleUpdate) {
        onTitleUpdate(payload.title);
      }
    }
  }
}

async function registerUser(email, password) {
  const response = await fetch(`${API_BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Erro ao cadastrar.");
  }
  return data;
}

async function loginUser(email, password) {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Erro ao fazer login.");
  }
  return data;
}

async function logoutUser(token) {
  const response = await fetch(`${API_BASE}/api/auth/logout`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Erro ao fazer logout.");
  }
  return data;
}

async function listSessions(token) {
  const response = await fetch(`${API_BASE}/api/sessions`, {
    method: "GET",
    headers: { "Authorization": `Bearer ${token}` },
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Erro ao listar sessoes.");
  }
  const data = await response.json();
  return data.sessions;
}

async function createSession(token, sessionKey) {
  const response = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
    body: JSON.stringify({ session_key: sessionKey }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Erro ao criar sessao.");
  }
  return data;
}

async function deleteSession(token, sessionKey) {
  const response = await fetch(`${API_BASE}/api/sessions/${sessionKey}`, {
    method: "DELETE",
    headers: { "Authorization": `Bearer ${token}` },
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Erro ao deletar sessao.");
  }
}

async function getSessionMessages(token, sessionKey) {
  const response = await fetch(`${API_BASE}/api/sessions/${sessionKey}/messages`, {
    method: "GET",
    headers: { "Authorization": `Bearer ${token}` },
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Erro ao carregar mensagens.");
  }
  const data = await response.json();
  return data.messages;
}
