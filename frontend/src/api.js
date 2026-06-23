const API_BASE = window.location.origin;

// ── Device Fingerprint ─────────────────────────────────────────

function getDeviceFingerprint() {
  const data = [
    navigator.userAgent,
    screen.width,
    screen.height,
    screen.colorDepth,
    navigator.language,
    navigator.platform,
    navigator.hardwareConcurrency,
    navigator.deviceMemory || "",
  ].join("|||");

  // Canvas fingerprint
  let canvasData = "";
  try {
    const canvas = document.createElement("canvas");
    canvas.width = 200;
    canvas.height = 50;
    const ctx = canvas.getContext("2d");
    ctx.textBaseline = "top";
    ctx.font = "14px Arial";
    ctx.fillStyle = "#f60";
    ctx.fillRect(125, 1, 62, 20);
    ctx.fillStyle = "#069";
    ctx.fillText("ChatLLM", 2, 15);
    canvasData = canvas.toDataURL();
  } catch (_) {
    canvasData = "canvas-not-available";
  }

  const raw = data + "|||" + canvasData;
  let hash = 0;
  for (let i = 0; i < raw.length; i++) {
    const chr = raw.charCodeAt(i);
    hash = ((hash << 5) - hash) + chr;
    hash |= 0;
  }
  return "fp_" + Math.abs(hash).toString(36);
}

// ── Auth API ───────────────────────────────────────────────────

async function apiRegister(email, password) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.detail || "Erro ao cadastrar.");
  return body;
}

async function apiLogin(email, password) {
  const deviceFingerprint = getDeviceFingerprint();
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, device_fingerprint: deviceFingerprint }),
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.detail || "Erro ao fazer login.");
  return body;
}

async function apiLogout(email, token) {
  const res = await fetch(`${API_BASE}/auth/logout`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, token }),
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.detail || "Erro ao fazer logout.");
  return body;
}

async function apiMe(token) {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { "Authorization": `Bearer ${token}` },
  });
  if (!res.ok) return null;
  const body = await res.json();
  return body;
}

// ── Chat API ───────────────────────────────────────────────────

async function sendMessageStream({ message, history, onDelta, signal }) {
  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
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
