const { useEffect, useMemo, useRef, useState, useCallback } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function App() {
  const [auth, setAuth] = useState(() => getStoredAuth());
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);

  const chatHistory = useMemo(
    () => messages.filter((msg) => msg.role === "user" || msg.role === "assistant"),
    [messages]
  );

  // ── Load sessions when auth changes ───────────────────────
  useEffect(() => {
    if (auth) {
      apiListSessions(auth.email).then(setSessions).catch(() => {});
    }
  }, [auth]);

  useEffect(() => {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  // ── Se nao estiver autenticado, mostra tela de login ──────────
  if (!auth) {
    return <AuthScreen onAuthSuccess={(email, token) => setAuth({ email, token })} />;
  }

  const onStop = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setBusy(false);
  };

  const onLogout = async () => {
    try {
      await apiLogout(auth.email, auth.token);
    } catch (_) {}
    clearStoredAuth();
    setAuth(null);
  };

  const switchSession = useCallback(async (sessionId) => {
    if (busy) return;
    setError("");
    setMessages([]);
    setCurrentSessionId(sessionId);
    setSidebarOpen(false);
    try {
      const msgs = await apiGetSessionMessages(sessionId, auth.email);
      setMessages(
        msgs.map((m) => ({
          id: createMessageId(),
          role: m.role,
          content: m.content,
        }))
      );
    } catch (err) {
      setError(err.message);
    }
  }, [auth, busy]);

  const newSession = useCallback(async () => {
    if (busy) return;
    setError("");
    setMessages([]);
    setCurrentSessionId(null);
    setSidebarOpen(false);
    // Refresh list
    const list = await apiListSessions(auth.email);
    setSessions(list);
  }, [auth, busy]);

  const deleteSession = useCallback(async (sessionId) => {
    try {
      await apiDeleteSession(sessionId, auth.email);
      const list = await apiListSessions(auth.email);
      setSessions(list);
      if (currentSessionId === sessionId) {
        setMessages([]);
        setCurrentSessionId(null);
      }
    } catch (err) {
      setError(err.message);
    }
  }, [auth, currentSessionId]);

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

    let newSessionId = currentSessionId;

    try {
      await sendMessageStream({
        message: cleaned,
        history: chatHistory,
        sessionId: newSessionId,
        signal: abortController.signal,
        onDelta: (delta, sessionId, title) => {
          if (sessionId && !newSessionId) {
            newSessionId = sessionId;
            setCurrentSessionId(sessionId);
          }
          if (delta) {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: `${msg.content}${delta}` }
                  : msg
              )
            );
          }
          if (title) {
            setSessions((prev) =>
              prev.map((s) =>
                s.id === newSessionId ? { ...s, title } : s
              )
            );
          }
        },
      });

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId && !msg.content.trim()
            ? { ...msg, content: "Nao foi possivel obter resposta do modelo agora." }
            : msg
        )
      );

      // Refresh sessions list
      const list = await apiListSessions(auth.email);
      setSessions(list);
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

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={newSession} disabled={busy}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="8" y1="2" x2="8" y2="14" />
              <line x1="2" y1="8" x2="14" y2="8" />
            </svg>
            Novo chat
          </button>
        </div>
        <div className="sidebar-list">
          {sessions.length === 0 && (
            <div className="sidebar-empty">Nenhuma sessao ainda</div>
          )}
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`sidebar-item ${s.id === currentSessionId ? "active" : ""}`}
              onClick={() => switchSession(s.id)}
            >
              <span className="sidebar-item-title">
                {s.title || "Nova sessao..."}
              </span>
              <button
                className="sidebar-item-del"
                onClick={(e) => { e.stopPropagation(); deleteSession(s.id); }}
                title="Excluir sessao"
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <line x1="2" y1="2" x2="10" y2="10" />
                  <line x1="10" y1="2" x2="2" y2="10" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* Overlay para mobile */}
      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}

      {/* Main area */}
      <main className="app-shell">
        <header className="app-header">
          <div className="header-left">
            <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)} aria-label="Menu">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="2" y1="4" x2="16" y2="4" />
                <line x1="2" y1="9" x2="16" y2="9" />
                <line x1="2" y1="14" x2="16" y2="14" />
              </svg>
            </button>
            <div className="brand">ChatLLM Lab</div>
          </div>
          <div className="auth-info">
            <span className="auth-email">{auth.email}</span>
            <button className="logout-btn" onClick={onLogout}>Sair</button>
          </div>
        </header>

        <section className="messages" aria-live="polite" ref={messagesRef}>
          <div className="messages-inner">
            {messages.length === 0 && (
              <div className="welcome-msg">
                {currentSessionId ? "Selecione uma sessao ou crie um novo chat." : "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?"}
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

        <div className="warning-banner">Lembre-se, voce precisa focar no experimento!!!</div>
      </main>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

