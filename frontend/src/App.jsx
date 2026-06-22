const { useEffect, useMemo, useRef, useState, useCallback } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function AuthScreen({ onAuthSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!email.trim() || !password) {
      setError("Preencha email e senha.");
      return;
    }
    setLoading(true);
    try {
      const result = isLogin
        ? await apiLogin(email.trim(), password)
        : await apiRegister(email.trim(), password);
      setAuth(result.access_token, result.email);
      onAuthSuccess();
    } catch (err) {
      setError(err.message || "Erro inesperado.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-screen">
      <div className="auth-card">
        <h1 className="auth-title">ChatLLM Lab</h1>
        <p className="auth-subtitle">{isLogin ? "Faça login para continuar" : "Crie sua conta"}</p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="auth-input"
            autoFocus
            disabled={loading}
          />
          <input
            type="password"
            placeholder="Senha (mín. 6 caracteres)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="auth-input"
            disabled={loading}
            minLength={6}
          />
          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? "Aguarde..." : isLogin ? "Entrar" : "Cadastrar"}
          </button>
        </form>

        <p className="auth-toggle">
          {isLogin ? "Não tem conta?" : "Já tem conta?"}{" "}
          <button className="auth-link-btn" onClick={() => { setIsLogin(!isLogin); setError(""); }}>
            {isLogin ? "Cadastre-se" : "Fazer login"}
          </button>
        </p>
      </div>
    </main>
  );
}

function Sidebar({ sessions, currentSessionId, onSelectSession, onNewSession, onDeleteSession, onRenameSession }) {
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");
  const inputRef = useRef(null);

  useEffect(() => {
    if (editingId !== null) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [editingId]);

  const handleDoubleClick = (session) => {
    setEditingId(session.id);
    setEditValue(session.title);
  };

  const handleSubmitEdit = async (sessionId) => {
    const trimmed = editValue.trim();
    if (trimmed && trimmed !== sessions.find(s => s.id === sessionId)?.title) {
      await onRenameSession(sessionId, trimmed);
    }
    setEditingId(null);
  };

  const handleKeyDown = (e, sessionId) => {
    if (e.key === "Enter") {
      handleSubmitEdit(sessionId);
    } else if (e.key === "Escape") {
      setEditingId(null);
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onNewSession}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="8" y1="2" x2="8" y2="14" />
            <line x1="2" y1="8" x2="14" y2="8" />
          </svg>
          Nova conversa
        </button>
      </div>
      <div className="sidebar-list">
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`sidebar-item ${s.id === currentSessionId ? "active" : ""}`}
            onClick={() => { if (editingId !== s.id) onSelectSession(s.id); }}
          >
            {editingId === s.id ? (
              <input
                ref={inputRef}
                className="sidebar-edit-input"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onBlur={() => handleSubmitEdit(s.id)}
                onKeyDown={(e) => handleKeyDown(e, s.id)}
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              <span
                className="sidebar-item-title"
                onDoubleClick={() => handleDoubleClick(s)}
                title="Duplo clique para editar"
              >
                {s.title}
              </span>
            )}
            <button
              className="sidebar-item-del"
              onClick={(e) => { e.stopPropagation(); onDeleteSession(s.id); }}
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
    </aside>
  );
}

function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Sessions
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);

  // Messages for the current session
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

  // Load sessions on auth
  const loadSessions = useCallback(async () => {
    const list = await apiListSessions();
    setSessions(list);
    if (list.length > 0 && !currentSessionId) {
      setCurrentSessionId(list[0].id);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated()) {
      apiMe().then((user) => {
        if (user) {
          setAuthenticated(true);
          loadSessions();
        } else {
          clearAuth();
        }
        setCheckingAuth(false);
      });
    } else {
      setCheckingAuth(false);
    }
  }, []);

  // Load messages when session changes
  useEffect(() => {
    if (!currentSessionId) {
      setMessages([]);
      return;
    }
    apiGetSessionMessages(currentSessionId).then((msgs) => {
      setMessages(
        msgs.length > 0
          ? msgs.map((m) => ({ id: createMessageId(), role: m.role, content: m.content }))
          : [
              {
                id: createMessageId(),
                role: "assistant",
                content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?",
              },
            ]
      );
    });
  }, [currentSessionId]);

  useEffect(() => {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const onStop = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setBusy(false);
  };

  const handleNewSession = async () => {
    const session = await apiCreateSession();
    setSessions((prev) => [session, ...prev]);
    setCurrentSessionId(session.id);
  };

  const handleSelectSession = (sessionId) => {
    if (busy) return;
    setCurrentSessionId(sessionId);
  };

  const handleDeleteSession = async (sessionId) => {
    await apiDeleteSession(sessionId);
    setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    if (currentSessionId === sessionId) {
      const remaining = sessions.filter((s) => s.id !== sessionId);
      setCurrentSessionId(remaining.length > 0 ? remaining[0].id : null);
    }
  };

  const handleRenameSession = async (sessionId, newTitle) => {
    await apiUpdateSessionTitle(sessionId, newTitle);
    setSessions((prev) =>
      prev.map((s) => (s.id === sessionId ? { ...s, title: newTitle } : s))
    );
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
      const sessionInfo = await sendMessageStream({
        message: cleaned,
        sessionId: currentSessionId,
        history: chatHistory,
        signal: abortController.signal,
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

      // Update session info if newly created or title changed
      if (sessionInfo) {
        if (!currentSessionId) {
          setCurrentSessionId(sessionInfo.id);
        }
      }
      // Always refresh sessions list to pick up auto-generated titles
      const list = await apiListSessions();
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

  const handleLogout = async () => {
    await apiLogout();
    setAuthenticated(false);
    setMessages([]);
    setSessions([]);
    setCurrentSessionId(null);
  };

  if (checkingAuth) {
    return (
      <main className="app-shell">
        <div className="auth-loading">Verificando autenticacao...</div>
      </main>
    );
  }

  if (!authenticated) {
    return <AuthScreen onAuthSuccess={() => { setAuthenticated(true); loadSessions(); }} />;
  }

  return (
    <div className="app-with-sidebar">
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        onRenameSession={handleRenameSession}
      />

      <main className="app-shell">
        <header className="app-header">
          <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="3" y1="4" x2="15" y2="4" />
              <line x1="3" y1="9" x2="15" y2="9" />
              <line x1="3" y1="14" x2="15" y2="14" />
            </svg>
          </button>
          <div className="brand">ChatLLM Lab</div>
          <div className="header-right">
            <span className="header-email">{getEmail()}</span>
            <button className="logout-btn" onClick={handleLogout}>Sair</button>
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

        <div className="warning-banner">Lembre-se, voce precisa focar no experimento!!!</div>
      </main>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

