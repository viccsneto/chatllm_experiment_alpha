const { useEffect, useMemo, useRef, useState } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

const WELCOME_MESSAGE = {
  id: createMessageId(),
  role: "assistant",
  content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?",
};

function App() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [user, setUserState] = useState(getUser);
  const [authMode, setAuthMode] = useState(null);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);

  const isLoggedIn = !!user;
  const chatHistory = useMemo(
    () => messages.filter((msg) => msg.role === "user" || msg.role === "assistant"),
    [messages]
  );

  useEffect(() => {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const onAuthSuccess = (data) => {
    setToken(data.access_token);
    setUser(data.user);
    setUserState(data.user);
    setAuthMode(null);
  };

  const onAuthCancel = (nextMode) => {
    if (nextMode === "login" || nextMode === "register") {
      setAuthMode(nextMode);
    } else {
      setAuthMode(null);
    }
  };

  const onLogout = () => {
    clearToken();
    clearUser();
    setUserState(null);
    setCurrentSessionId(null);
    setMessages([WELCOME_MESSAGE]);
  };

  const onSelectSession = async (sessionId) => {
    if (sessionId === currentSessionId) return;
    setCurrentSessionId(sessionId);
    setMessages([WELCOME_MESSAGE]);
    if (sessionId) {
      try {
        const msgs = await getSessionMessages(sessionId);
        if (msgs && msgs.length > 0) {
          setMessages(
            msgs.map((m) => ({
              id: createMessageId(),
              role: m.role,
              content: m.content,
            }))
          );
        }
      } catch {
        // silently fail
      }
    }
  };

  const onNewSession = () => {
    setCurrentSessionId(null);
    setMessages([WELCOME_MESSAGE]);
  };

  const onDeleteSession = async (sessionId) => {
    try {
      await deleteSession(sessionId);
    } catch {
      // silently fail
    }
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
      const newSessionId = await sendMessageStream({
        message: cleaned,
        history: chatHistory,
        sessionId: currentSessionId,
        signal: abortController.signal,
        onDelta: (delta, sid) => {
          if (sid && sid !== currentSessionId) {
            setCurrentSessionId(sid);
          }
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: `${msg.content}${delta}` }
                : msg
            )
          );
        },
      });

      if (newSessionId && newSessionId !== currentSessionId) {
        setCurrentSessionId(newSessionId);
      }

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

  if (authMode) {
    return (
      <Auth
        mode={authMode}
        onSuccess={onAuthSuccess}
        onCancel={onAuthCancel}
      />
    );
  }

  return (
    <main className="app-shell">
      {isLoggedIn && (
        <div className={`sidebar-overlay ${sidebarOpen ? "open" : ""}`} onClick={() => setSidebarOpen(false)} />
      )}
      {isLoggedIn && (
        <div className={`sidebar-wrapper ${sidebarOpen ? "open" : ""}`}>
          <Sidebar
            activeSessionId={currentSessionId}
            onSelectSession={onSelectSession}
            onNewSession={onNewSession}
            onDeleteSession={onDeleteSession}
          />
        </div>
      )}
      <div className="main-content">
        <header className="app-header">
          <div className="header-left">
            {isLoggedIn && (
              <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)} title="Sessoes">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <line x1="2" y1="4" x2="16" y2="4" />
                  <line x1="2" y1="9" x2="16" y2="9" />
                  <line x1="2" y1="14" x2="16" y2="14" />
                </svg>
              </button>
            )}
            <div className="brand">ChatLLM Lab</div>
          </div>
          <div className="auth-toolbar">
            {isLoggedIn ? (
              <>
                <span className="auth-email">{user.email}</span>
                <button className="auth-toolbar-btn" onClick={onLogout}>Logout</button>
              </>
            ) : (
              <>
                <button className="auth-toolbar-btn" onClick={() => setAuthMode("login")}>Login</button>
                <button className="auth-toolbar-btn" onClick={() => setAuthMode("register")}>Cadastro</button>
              </>
            )}
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
      </div>
    </main>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

