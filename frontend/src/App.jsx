const { useEffect, useMemo, useRef, useState } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function AuthScreen({ onAuthSuccess }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setAuthError("");
    setLoading(true);
    try {
      const fn = mode === "login" ? apiLogin : apiSignup;
      const data = await fn(email, password);
      setToken(data.token);
      onAuthSuccess(data.email);
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="app-shell">
      <div className="auth-center">
        <form className="auth-form" onSubmit={handleSubmit}>
          <h1 className="auth-title">ChatLLM Lab</h1>
          <p className="auth-subtitle">{mode === "login" ? "Entre na sua conta" : "Crie sua conta"}</p>

          {authError && <div className="auth-error">{authError}</div>}

          <input
            className="auth-input"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
          <input
            className="auth-input"
            type="password"
            placeholder="Senha"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />

          <button className="auth-btn" type="submit" disabled={loading}>
            {loading ? "Aguarde..." : mode === "login" ? "Entrar" : "Cadastrar"}
          </button>

          <p className="auth-toggle">
            {mode === "login" ? (
              <>Nao tem conta? <a href="#" onClick={(e) => { e.preventDefault(); setMode("signup"); setAuthError(""); }}>Cadastre-se</a></>
            ) : (
              <>Ja tem conta? <a href="#" onClick={(e) => { e.preventDefault(); setMode("login"); setAuthError(""); }}>Faca login</a></>
            )}
          </p>
        </form>
      </div>
    </main>
  );
}

function Sidebar({ sessions, activeSessionId, onSelectSession, onNewSession, onDeleteSession }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onNewSession}>
          + Nova conversa
        </button>
      </div>
      <div className="sidebar-list">
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`sidebar-item ${s.id === activeSessionId ? "active" : ""}`}
            onClick={() => onSelectSession(s.id)}
          >
            <span className="sidebar-item-title">
              {s.title || "Nova conversa"}
            </span>
            <button
              className="sidebar-item-delete"
              onClick={(e) => { e.stopPropagation(); onDeleteSession(s.id); }}
              title="Excluir"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}

function ChatApp({ email, onLogout }) {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);

  const loadSessions = async () => {
    const list = await apiListSessions();
    setSessions(list);
  };

  useEffect(() => { loadSessions(); }, []);

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

  const loadMessages = async (sessionId) => {
    setActiveSessionId(sessionId);
    setMessages([]);
    setError("");
    const msgs = await apiListMessages(sessionId);
    setMessages(
      msgs.length > 0
        ? msgs.map((m) => ({ id: createMessageId(), role: m.role, content: m.content }))
        : [{ id: createMessageId(), role: "assistant", content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?" }]
    );
  };

  const handleNewSession = async () => {
    const sess = await apiCreateSession();
    setSessions((prev) => [sess, ...prev]);
    loadMessages(sess.id);
  };

  const handleDeleteSession = async (sessionId) => {
    await apiDeleteSession(sessionId);
    setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    if (activeSessionId === sessionId) {
      setActiveSessionId(null);
      setMessages([]);
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

    if (!activeSessionId) {
      const sess = await apiCreateSession();
      setSessions((prev) => [sess, ...prev]);
      setActiveSessionId(sess.id);
    }

    setError("");
    const userMessage = { id: createMessageId(), role: "user", content: cleaned };
    const assistantMessageId = createMessageId();
    const currentSessionId = activeSessionId;

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
        sessionId: currentSessionId,
        signal: abortController.signal,
        onSessionId: (sid) => {
          if (!currentSessionId) {
            setActiveSessionId(sid);
          }
        },
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

      // Recarrega sessoes para pegar o titulo automatico
      await loadSessions();
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
    try { await apiLogout(); } catch { /* ignore */ }
    onLogout();
  };

  return (
    <div className="app-layout">
      {sidebarOpen && (
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={loadMessages}
          onNewSession={handleNewSession}
          onDeleteSession={handleDeleteSession}
        />
      )}
      <main className="app-shell">
        <header className="app-header">
          <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? "\u2630" : "\u2630"}
          </button>
          <div className="brand">ChatLLM Lab</div>
          <div className="header-right">
            <span className="header-email">{email}</span>
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

function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setChecking(false);
      return;
    }
    apiMe()
      .then((data) => {
        if (data) setUser(data.email);
        else clearToken();
      })
      .catch(() => clearToken())
      .finally(() => setChecking(false));
  }, []);

  if (checking) {
    return <main className="app-shell"><div className="auth-center"><p>Verificando sessao...</p></div></main>;
  }

  if (!user) {
    return <AuthScreen onAuthSuccess={(email) => setUser(email)} />;
  }

  return <ChatApp email={user} onLogout={() => setUser(null)} />;
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

