const { useEffect, useMemo, useRef, useState } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

/* ── Auth Screen ──────────────────────────────────────── */

function AuthScreen({ onAuth }) {
  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const fn = mode === "login" ? login : signup;
      const data = await fn(email, password);
      onAuth(data.token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand">ChatLLM Lab</div>
      </header>
      <div style={{
        flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
        padding: "24px",
      }}>
        <form onSubmit={handleSubmit} style={{
          width: "100%", maxWidth: 360, display: "flex", flexDirection: "column", gap: 16,
        }}>
          <h2 style={{ margin: 0, fontSize: "1.25rem", textAlign: "center" }}>
            {mode === "login" ? "Entrar" : "Criar Conta"}
          </h2>

          {error && (
            <div style={{ color: "#c0392b", fontSize: "0.875rem", textAlign: "center" }}>
              {error}
            </div>
          )}

          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{
              padding: "10px 14px", borderRadius: 8, border: "1px solid var(--composer-border)",
              font: "inherit", fontSize: "0.95rem",
            }}
          />
          <input
            type="password"
            placeholder="Senha"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            style={{
              padding: "10px 14px", borderRadius: 8, border: "1px solid var(--composer-border)",
              font: "inherit", fontSize: "0.95rem",
            }}
          />

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: "10px", borderRadius: 8, border: "none",
              background: "var(--accent)", color: "#fff", fontWeight: 600,
              cursor: "pointer", fontSize: "0.95rem",
            }}
          >
            {loading ? "Aguarde..." : mode === "login" ? "Entrar" : "Cadastrar"}
          </button>

          <button
            type="button"
            onClick={() => { setMode(mode === "login" ? "signup" : "login"); setError(""); }}
            style={{
              background: "none", border: "none", color: "var(--muted)",
              cursor: "pointer", fontSize: "0.85rem", textDecoration: "underline",
            }}
          >
            {mode === "login" ? "Nao tem conta? Cadastre-se" : "Ja tem conta? Entrar"}
          </button>
        </form>
      </div>
    </main>
  );
}

/* ── Main App ─────────────────────────────────────────── */

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("auth_token"));
  const [user, setUser] = useState(null);

  const [messages, setMessages] = useState([
    {
      id: createMessageId(),
      role: "assistant",
      content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?",
    },
  ]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);

  const chatHistory = useMemo(
    () => messages.filter((msg) => msg.role === "user" || msg.role === "assistant"),
    [messages]
  );

  /* Restore session on mount */
  useEffect(() => {
    if (token) {
      getMe(token)
        .then((u) => setUser(u))
        .catch(() => {
          localStorage.removeItem("auth_token");
          setToken(null);
        });
    }
  }, []);

  useEffect(() => {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const handleAuth = (newToken) => {
    localStorage.setItem("auth_token", newToken);
    setToken(newToken);
    getMe(newToken).then((u) => setUser(u)).catch(() => {});
  };

  const handleLogout = async () => {
    try {
      await logout(token);
    } catch { /* ignore */ }
    localStorage.removeItem("auth_token");
    setToken(null);
    setUser(null);
    setMessages([
      {
        id: createMessageId(),
        role: "assistant",
        content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?",
      },
    ]);
  };

  const onStop = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setBusy(false);
  };

  const onSubmit = async (event, inputRef) => {
    event.preventDefault();
    const cleaned = text.trim();
    if (!cleaned || busy) return;

    setError("");
    const userMessage = { id: createMessageId(), role: "user", content: cleaned };
    const assistantMessageId = createMessageId();

    setMessages((prev) => [
      ...prev,
      userMessage,
      { id: assistantMessageId, role: "assistant", content: "" },
    ]);
    setText("");
    setBusy(true);
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      await sendMessageStream({
        message: cleaned,
        history: chatHistory,
        signal: abortController.signal,
        token,
        onDelta: (delta) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: `${msg.content}${delta}` }
                : msg
            )
          );
        },
      });

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId && !msg.content.trim()
            ? { ...msg, content: "Nao foi possivel obter resposta do modelo agora." }
            : msg
        )
      );
    } catch (err) {
      const aborted = err?.name === "AbortError";
      if (!aborted) {
        setError(err.message || "Falha inesperada ao gerar resposta.");
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: msg.content.trim() ? msg.content : "Nao foi possivel obter resposta do modelo agora." }
              : msg
          )
        );
      } else {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId && !msg.content.trim()
              ? { ...msg, content: "Resposta interrompida." }
              : msg
          )
        );
      }
    } finally {
      abortControllerRef.current = null;
      setBusy(false);
    }
  };

  /* ── Not authenticated → show auth screen ── */
  if (!token) {
    return <AuthScreen onAuth={handleAuth} />;
  }

  return (
    <main className="app-shell">
      <header className="app-header" style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <div className="brand">ChatLLM Lab</div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
            {user?.email || ""}
          </span>
          <button
            onClick={handleLogout}
            style={{
              background: "none", border: "1px solid var(--border)", borderRadius: 8,
              padding: "4px 12px", cursor: "pointer", fontSize: "0.8rem", color: "var(--text)",
            }}
          >
            Sair
          </button>
        </div>
      </header>

      <section className="messages" aria-live="polite" ref={messagesRef}>
        <div className="messages-inner">
          {messages.map((msg) => (
            <article key={msg.id} className={`bubble ${msg.role}`}>
              <MessageContent content={msg.content} />
            </article>
          ))}
        </div>
      </section>

      <Composer
        text={text}
        busy={busy}
        error={error}
        onChangeText={setText}
        onSubmit={onSubmit}
        onStop={onStop}
      />

      <div className="warning-banner">Lembre-se, você precisa focar no experimento!!!</div>
    </main>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

