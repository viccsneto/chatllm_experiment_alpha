const API_BASE = window.location.origin;

function getAuthHeaders() {
  const token = localStorage.getItem("access_token");
  return token ? { "Authorization": `Bearer ${token}` } : {};
}

async function apiPost(path, body, useAuth = false) {
  const headers = { "Content-Type": "application/json" };
  if (useAuth) Object.assign(headers, getAuthHeaders());

  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("Erro inesperado no servidor. Tente novamente ou verifique se o servidor esta rodando.");
  }

  if (!response.ok) {
    throw new Error(data.detail || "Erro na requisicao.");
  }
  return data;
}

async function apiGet(path) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { ...getAuthHeaders() },
  });

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("Erro inesperado no servidor. Tente novamente ou verifique se o servidor esta rodando.");
  }

  if (!response.ok) {
    throw new Error(data.detail || "Erro na requisicao.");
  }
  return data;
}

async function signup({ name, email, password, security_question, security_answer }) {
  return apiPost("/api/auth/signup", { name, email, password, security_question, security_answer });
}

async function login({ email, password }) {
  return apiPost("/api/auth/login", { email, password });
}

async function forgotPassword({ email }) {
  return apiPost("/api/auth/forgot-password", { email });
}

async function verifySecurityAnswer({ email, security_answer }) {
  return apiPost("/api/auth/verify-security-answer", { email, security_answer });
}

async function resetPassword({ email, new_password }) {
  return apiPost("/api/auth/reset-password", { email, new_password });
}

async function logout() {
  return apiPost("/api/auth/logout", {});
}

async function getMe() {
  return apiGet("/api/auth/me");
}

async function sendMessageStream({ message, history, onDelta, signal }) {
  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ message, history }),
    signal,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body?.detail || "Erro ao enviar mensagem para o servidor. Verifique se voce esta logado.";
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
