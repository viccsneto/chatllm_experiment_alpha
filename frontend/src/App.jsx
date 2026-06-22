const { useEffect, useMemo, useRef, useState } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function App() {
  const [userEmail, setUserEmail] = useState(null);
  const [authMode, setAuthMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authBusy, setAuthBusy] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [activeSessionKey, setActiveSessionKey] = useState(null);
  const [activeSessionTitle, setActiveSessionTitle] = useState("Nova conversa");
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
  const [loadingSession, setLoadingSession] = useState(false);
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);

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

  useEffect(() => {
    async function loadUser() {
      try {
        const data = await window.getCurrentUser();
        setUserEmail(data.email);
      } catch {
        setUserEmail(null);
      }
    }

    loadUser();
  }, []);

  useEffect(() => {
    if (!userEmail) {
      setSessions([]);
      setActiveSessionKey(null);
      setActiveSessionTitle("Nova conversa");
      setMessages([
        {
          id: createMessageId(),
          role: "assistant",
          content: "Faça login para acessar suas conversas.",
        },
      ]);
      return;
    }

    loadSessions();
  }, [userEmail]);

  const authAction = authMode === "login" ? window.login : window.signup;

  const updateSessionTitle = (sessionKey, title) => {
    setSessions((prev) =>
      prev.map((session) =>
        session.key === sessionKey ? { ...session, title } : session
      )
    );
  };

  const loadSession = async (sessionKey, existingSessions) => {
    setLoadingSession(true);
    setError("");

    try {
      const session = await window.getChatSession(sessionKey);
      setActiveSessionKey(session.key);
      setActiveSessionTitle(session.title || "Nova conversa");
      setMessages(
        session.messages.map((message) => ({
          id: createMessageId(),
          role: message.role,
          content: message.content,
        }))
      );
      if (existingSessions) {
        setSessions(existingSessions);
      }
    } catch (err) {
      setError(err.message || "Falha ao carregar a sessão.");
    } finally {
      setLoadingSession(false);
    }
  };

  const loadSessions = async () => {
    setLoadingSession(true);
    setError("");

    try {
      let savedSessions = await window.fetchChatSessions();
      if (savedSessions.length === 0) {
        const newSession = await window.createChatSession();
        savedSessions = [newSession];
      }
      setSessions(savedSessions);

      const sessionToOpen = activeSessionKey || savedSessions[0]?.key;
      if (sessionToOpen) {
        await loadSession(sessionToOpen, savedSessions);
      }
    } catch (err) {
      setError(err.message || "Falha ao carregar sessões.");
    } finally {
      setLoadingSession(false);
    }
  };

  const createSession = async () => {
    if (busy || loadingSession) return;
    setLoadingSession(true);
    setError("");

    try {
      const created = await window.createChatSession();
      setSessions((prev) => [created, ...prev]);
      setActiveSessionKey(created.key);
      setActiveSessionTitle(created.title || "Nova conversa");
      setMessages([]);
    } catch (err) {
      setError(err.message || "Falha ao criar nova sessão.");
    } finally {
      setLoadingSession(false);
    }
  };

  const selectSession = async (sessionKey) => {
    if (sessionKey === activeSessionKey) return;
    await loadSession(sessionKey);
  };

  const onAuthSubmit = async (event) => {
    event.preventDefault();
    if (authBusy || !email.trim() || !password.trim()) return;

    setAuthError("");
    setAuthBusy(true);

    try {
      await authAction({ email: email.trim(), password });
      const data = await window.getCurrentUser();
      setUserEmail(data.email);
      setEmail("");
      setPassword("");
    } catch (err) {
      setAuthError(err.message || "Falha ao autenticar.");
    } finally {
      setAuthBusy(false);
    }
  };

  const onLogout = async () => {
    setAuthError("");
    setAuthBusy(true);

    try {
      await window.logout();
      setUserEmail(null);
      setMessages([
        {
          id: createMessageId(),
          role: "assistant",
          content: "Voce saiu. Faça login para usar o ChatLLM Lab.",
        },
      ]);
      setSessions([]);
      setActiveSessionKey(null);
      setActiveSessionTitle("Nova conversa");
    } catch (err) {
      setAuthError(err.message || "Falha ao fazer logout.");
    } finally {
      setAuthBusy(false);
    }
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    const cleaned = text.trim();
    if (!cleaned || busy || authBusy || !activeSessionKey) return;

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
      await window.sendMessageStream({
        message: cleaned,
        history: chatHistory,
        sessionKey: activeSessionKey,
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
        onDone: (payload) => {
          if (payload.session_title) {
            setActiveSessionTitle(payload.session_title);
            updateSessionTitle(payload.session_key, payload.session_title);
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

  if (!userEmail) {
    return (
      <main className="app-shell">
        <header className="app-header">
          <div className="brand">ChatLLM Lab</div>
        </header>

        <section className="auth-panel">
          <div className="auth-card">
            <h1>{authMode === "login" ? "Entrar" : "Criar conta"}</h1>
            <p className="note">Faça login ou cadastre-se para acessar o ChatLLM.</p>
            {authError && <div className="note error">{authError}</div>}
            <form className="auth-form" onSubmit={onAuthSubmit}>
              <label>
                Email
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="seu@email.com"
                  disabled={authBusy}
                  required
                />
              </label>
              <label>
                Senha
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Senha (mínimo 8 caracteres)"
                  disabled={authBusy}
                  required
                />
              </label>
              <button type="submit" disabled={authBusy || !email.trim() || !password.trim()}>
                {authBusy ? "Aguarde..." : authMode === "login" ? "Entrar" : "Criar conta"}
              </button>
            </form>
            <div className="auth-switch">
              {authMode === "login" ? "Nao tem conta?" : "Ja tem conta?"}
              <button
                type="button"
                className="ghost"
                onClick={() => {
                  setAuthMode(authMode === "login" ? "signup" : "login");
                  setAuthError("");
                }}
              >
                {authMode === "login" ? "Cadastre-se" : "Entrar"}
              </button>
            </div>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand">ChatLLM Lab</div>
        <div className="user-bar">
          <span>{userEmail}</span>
          <button type="button" onClick={onLogout} disabled={busy || authBusy}>
            Sair
          </button>
        </div>
      </header>

      <div className="app-body">
        <aside className="sidebar">
          <div className="sidebar-header">
            <span>Sessoes</span>
            <button type="button" className="secondary" onClick={createSession} disabled={loadingSession || busy}>
              Nova
            </button>
          </div>
          <div className="session-list">
            {loadingSession && <div className="note">Carregando sessões...</div>}
            {!loadingSession && sessions.length === 0 && <div className="note">Nenhuma sessão disponível.</div>}
            {sessions.map((session) => (
              <button
                key={session.key}
                type="button"
                className={`session-item ${session.key === activeSessionKey ? "active" : ""}`}
                onClick={() => selectSession(session.key)}
              >
                <strong>{session.title || "Nova conversa"}</strong>
                <span>{new Date(session.created_at).toLocaleString()}</span>
              </button>
            ))}
          </div>
        </aside>

        <section className="chat-column">
          <div className="chat-header">
            <div>
              <div className="session-title">{activeSessionTitle}</div>
              <div className="note">Sessão: {activeSessionKey || "sem sessão"}</div>
            </div>
          </div>

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
            onStop={() => {
              abortControllerRef.current?.abort();
              abortControllerRef.current = null;
              setBusy(false);
            }}
          />
          <div className="warning-banner">Lembre-se, você precisa focar no experimento!!!</div>
        </section>
      </div>
    </main>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

