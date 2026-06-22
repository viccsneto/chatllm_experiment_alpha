const API_BASE = window.location.origin;

async function fetchWithJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message = body?.detail || body?.message || "Erro ao comunicar com o servidor.";
    throw new Error(message);
  }

  return response.json();
}

window.signup = async function signup({ email, password }) {
  return fetchWithJson("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
};

window.login = async function login({ email, password }) {
  return fetchWithJson("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
};

window.logout = async function logout() {
  return fetchWithJson("/api/auth/logout", {
    method: "POST",
  });
};

window.getCurrentUser = async function getCurrentUser() {
  return fetchWithJson("/api/auth/me", {
    method: "GET",
  });
};

window.sendMessageStream = async function sendMessageStream({ message, history, onDelta, signal }) {
  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
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
