const { useEffect, useMemo, useRef, useState, useCallback } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

/* ── Auth Screen ──────────────────────────────────────── */

function AuthScreen({ onAuth }) {
  const [mode, setMode] = useState("login");
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
          <input type="email" placeholder="Email" value={email}
            onChange={(e) => setEmail(e.target.value)} required
            style={{ padding: "10px 14px", borderRadius: 8, border: "1px solid var(--composer-border)", font: "inherit", fontSize: "0.95rem" }}
          />
          <input type="password" placeholder="Senha" value={password}
            onChange={(e) => setPassword(e.target.value)} required minLength={6}
            style={{ padding: "10px 14px", borderRadius: 8, border: "1px solid var(--composer-border)", font: "inherit", fontSize: "0.95rem" }}
          />
          <button type="submit" disabled={loading}
            style={{ padding: "10px", borderRadius: 8, border: "none", background: "var(--accent)", color: "#fff", fontWeight: 600, cursor: "pointer", fontSize: "0.95rem" }}
          >
            {loading ? "Aguarde..." : mode === "login" ? "Entrar" : "Cadastrar"}
          </button>
          <button type="button"
            onClick={() => { setMode(mode === "login" ? "signup" : "login"); setError(""); }}
            style={{ background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: "0.85rem", textDecoration: "underline" }}
          >
            {mode === "login" ? "Nao tem conta? Cadastre-se" : "Ja tem conta? Entrar"}
          </button>
        </form>
      </div>
    </main>
  );
}

/* ── Sidebar ──────────────────────────────────────────── */

function Sidebar({ sessions, activeSessionId, onSelect, onCreate, onDelete, onLogout, userEmail }) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <button className="sidebar-new-btn" onClick={onCreate}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="7" y1="1" x2="7" y2="13" />
            <line x1="1" y1="7" x2="13" y2="7" />
          </svg>
          Nova conversa
        </button>
      </div>
      <div className="sidebar-list">
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`sidebar-item ${s.id === activeSessionId ? "active" : ""}`}
            onClick={() => onSelect(s.id)}
          >
            <span className="sidebar-item-title">{s.title}</span>
            <button
              className="sidebar-item-del"
              onClick={(e) => { e.stopPropagation(); onDelete(s.id); }}
              title="Deletar"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                <line x1="2" y1="2" x2="10" y2="10" />
                <line x1="10" y1="2" x2="2" y2="10" />
              </svg>
            </button>
          </div>
        ))}
      </div>
      <div className="sidebar-footer">
        <span className="sidebar-email">{userEmail}</span>
        <button className="sidebar-logout-btn" onClick={onLogout}>Sair</button>
      </div>
    </div>
  );
}

/* ── Main App ─────────────────────────────────────────── */

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("auth_token"));
  const [user, setUser] = useState(null);

  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const [messages, setMessages] = useState([]);
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

  /* Load sessions when user is set */
  useEffect(() => {
    if (token && user) {
      listSessions(token).then(setSessions).catch(() => {});
    }
  }, [token, user]);

  /* Load messages when active session changes */
  const loadMessages = useCallback(async (sessionId) => {
    if (!token || sessionId == null) return;
    try {
      const msgs = await getSessionMessages(token, sessionId);
      setMessages(msgs.map((m) => ({ id: createMessageId(), role: m.role, content: m.content })));
    } catch {
      setMessages([]);
    }
  }, [token]);

  useEffect(() => {
    if (activeSessionId != null) {
      loadMessages(activeSessionId);
    } else {
      setMessages([]);
    }
  }, [activeSessionId, loadMessages]);

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
    try { await logout(token); } catch { /* ignore */ }
    localStorage.removeItem("auth_token");
    setToken(null);
    setUser(null);
    setSessions([]);
    setActiveSessionId(null);
    setMessages([]);
  };

  const handleCreateSession = async () => {
    try {
      const s = await createSession(token);
      setSessions((prev) => [s, ...prev]);
      setActiveSessionId(s.id);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await deleteSession(token, sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([]);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSelectSession = (sessionId) => {
    setActiveSessionId(sessionId);
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

    // Auto-create session if none active
    let sessionId = activeSessionId;
    if (sessionId == null) {
      try {
        const s = await createSession(token);
        setSessions((prev) => [s, ...prev]);
        sessionId = s.id;
        setActiveSessionId(s.id);
      } catch (err) {
        setError(err.message);
        return;
      }
    }

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
        sessionId,
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

      // Refresh sessions to get updated title
      const updated = await listSessions(token);
      setSessions(updated);
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

  if (!token) {
    return <AuthScreen onAuth={handleAuth} />;
  }

  return (
    <div className="app-layout">
      {sidebarOpen && (
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelect={handleSelectSession}
          onCreate={handleCreateSession}
          onDelete={handleDeleteSession}
          onLogout={handleLogout}
          userEmail={user?.email || ""}
        />
      )}
      <main className="app-shell">
        <header className="app-header" style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              style={{ background: "none", border: "none", cursor: "pointer", padding: 4, color: "var(--text)" }}
              aria-label="Toggle sidebar"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="3" y1="4" x2="15" y2="4" />
                <line x1="3" y1="9" x2="15" y2="9" />
                <line x1="3" y1="14" x2="15" y2="14" />
              </svg>
            </button>
            <div className="brand">ChatLLM Lab</div>
          </div>
        </header>

        <section className="messages" aria-live="polite" ref={messagesRef}>
          <div className="messages-inner">
            {messages.length === 0 && (
              <div style={{ textAlign: "center", color: "var(--muted)", marginTop: 60, fontSize: "0.95rem" }}>
                Selecione uma conversa ou crie uma nova.
              </div>
            )}
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
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

