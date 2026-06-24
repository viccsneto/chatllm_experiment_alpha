const { useEffect, useMemo, useRef, useState, useCallback } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function generateSessionKey() {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

const AUTH_KEY = "chatllm_auth";

function getStoredAuth() {
  try {
    const raw = localStorage.getItem(AUTH_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function storeAuth(token, email) {
  localStorage.setItem(AUTH_KEY, JSON.stringify({ token, email }));
}

function clearAuth() {
  localStorage.removeItem(AUTH_KEY);
}

function App() {
  const [auth, setAuth] = useState(getStoredAuth);
  const [sessions, setSessions] = useState([]);
  const [activeSessionKey, setActiveSessionKey] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);
  const sessionsLoadedRef = useRef(false);

  const chatHistory = useMemo(
    () => messages.filter((msg) => msg.role === "user" || msg.role === "assistant"),
    [messages]
  );

  // Carregar sessoes ao montar
  useEffect(() => {
    if (!auth || sessionsLoadedRef.current) return;
    sessionsLoadedRef.current = true;

    listSessions(auth.token)
      .then((s) => {
        setSessions(s);
        if (s.length > 0) {
          setActiveSessionKey(s[0].session_key);
        }
      })
      .catch(() => {});
  }, [auth]);

  // Carregar mensagens ao trocar de sessao
  useEffect(() => {
    if (!auth || !activeSessionKey) return;

    getSessionMessages(auth.token, activeSessionKey)
      .then((msgs) => {
        if (msgs.length > 0) {
          setMessages(
            msgs.map((m) => ({
              id: createMessageId(),
              role: m.role,
              content: m.content,
            }))
          );
        } else {
          setMessages([
            {
              id: createMessageId(),
              role: "assistant",
              content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?",
            },
          ]);
        }
      })
      .catch(() => {
        setMessages([
          {
            id: createMessageId(),
            role: "assistant",
            content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?",
          },
        ]);
      });
  }, [auth, activeSessionKey]);

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

  const handleNewSession = useCallback(async () => {
    if (!auth) return;
    const key = generateSessionKey();
    try {
      const s = await createSession(auth.token, key);
      setSessions((prev) => [s, ...prev]);
      setActiveSessionKey(key);
      setMessages([
        {
          id: createMessageId(),
          role: "assistant",
          content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?",
        },
      ]);
    } catch (err) {
      setError(err.message);
    }
  }, [auth]);

  const handleSelectSession = useCallback((key) => {
    setActiveSessionKey(key);
    setError("");
  }, []);

  const handleDeleteSession = useCallback(async (key) => {
    if (!auth) return;
    try {
      await deleteSession(auth.token, key);
      setSessions((prev) => prev.filter((s) => s.session_key !== key));
      if (activeSessionKey === key) {
        const remaining = sessions.filter((s) => s.session_key !== key);
        if (remaining.length > 0) {
          setActiveSessionKey(remaining[0].session_key);
        } else {
          setActiveSessionKey(null);
          setMessages([
            {
              id: createMessageId(),
              role: "assistant",
              content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?",
            },
          ]);
        }
      }
    } catch (err) {
      setError(err.message);
    }
  }, [auth, activeSessionKey, sessions]);

  const handleTitleUpdate = useCallback((title) => {
    setSessions((prev) =>
      prev.map((s) =>
        s.session_key === activeSessionKey ? { ...s, title } : s
      )
    );
  }, [activeSessionKey]);

  const onSubmit = async (event, inputRef) => {
    event.preventDefault();
    const cleaned = text.trim();
    if (!cleaned || busy) return;

    // Se nao ha sessao ativa, cria uma
    let key = activeSessionKey;
    if (!key) {
      key = generateSessionKey();
      try {
        const s = await createSession(auth.token, key);
        setSessions((prev) => [s, ...prev]);
        setActiveSessionKey(key);
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
        sessionKey: key,
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
        onTitleUpdate: handleTitleUpdate,
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

  const handleAuthSuccess = (token, email) => {
    storeAuth(token, email);
    setAuth({ token, email });
  };

  const handleLogout = async () => {
    if (auth?.token) {
      try {
        await logoutUser(auth.token);
      } catch {
        // Continua mesmo se o logout no servidor falhar
      }
    }
    clearAuth();
    setAuth(null);
    sessionsLoadedRef.current = false;
    setSessions([]);
    setActiveSessionKey(null);
    setMessages([]);
  };

  if (!auth) {
    return <AuthPage onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <div className="app-layout">
      {!sidebarOpen && (
        <button className="sidebar-toggle" onClick={() => setSidebarOpen(true)} aria-label="Abrir sidebar">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="3" y1="4" x2="15" y2="4" />
            <line x1="3" y1="9" x2="15" y2="9" />
            <line x1="3" y1="14" x2="15" y2="14" />
          </svg>
        </button>
      )}

      <Sidebar
        sessions={sessions}
        activeKey={activeSessionKey}
        onSelect={handleSelectSession}
        onCreate={handleNewSession}
        onDelete={handleDeleteSession}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        open={sidebarOpen}
      />

      <main className="main-content">
        <div className="user-info">
          <span>
            Logado como <span className="user-email">{auth.email}</span>
          </span>
          <button className="logout-btn" onClick={handleLogout}>
            Sair
          </button>
        </div>

        <header className="app-header">
          <div className="brand">ChatLLM Lab</div>
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
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

