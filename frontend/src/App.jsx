const { useEffect, useMemo, useRef, useState } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function App() {
  const [user, setUser] = useState(null);
  const [loadingAuth, setLoadingAuth] = useState(true);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Verificar token al cargar
  useEffect(() => {
    (async () => {
      const token = localStorage.getItem("chatllm_token");
      if (token) {
        try {
          const data = await me();
          setUser(data.email);
        } catch {
          localStorage.removeItem("chatllm_token");
        }
      }
      setLoadingAuth(false);
    })();
  }, []);

  // Cargar sesiones cuando el usuario está autenticado
  useEffect(() => {
    if (!user) return;
    (async () => {
      try {
        const data = await getSessions();
        const list = data.sessions || [];
        setSessions(list);
        if (list.length > 0) {
          setCurrentSessionId(list[0].id);
          loadMessages(list[0].id);
        } else {
          const ns = await createSession();
          setSessions([ns]);
          setCurrentSessionId(ns.id);
          setMessages([{
            id: createMessageId(), role: "assistant",
            content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?",
          }]);
        }
      } catch (err) {
        setError(err.message);
      }
    })();
  }, [user]);

  const loadMessages = async (sessionId) => {
    setCurrentSessionId(sessionId);
    try {
      const data = await getSessionMessages(sessionId);
      const msgs = data.messages && data.messages.length > 0
        ? data.messages.map((m) => ({ id: createMessageId(), role: m.role, content: m.content }))
        : [{ id: createMessageId(), role: "assistant", content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?" }];
      setMessages(msgs);
    } catch {
      setMessages([{ id: createMessageId(), role: "assistant", content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?" }]);
    }
  };

  const handleAuthSuccess = (email) => {
    setUser(email);
  };

  const handleLogout = () => {
    localStorage.removeItem("chatllm_token");
    setUser(null);
    setSessions([]);
    setCurrentSessionId(null);
    setMessages([]);
  };

  const handleSelectSession = (sessionId) => {
    loadMessages(sessionId);
  };

  const handleCreateSession = async () => {
    try {
      const ns = await createSession();
      setSessions((prev) => [ns, ...prev]);
      setCurrentSessionId(ns.id);
      setMessages([{ id: createMessageId(), role: "assistant", content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?" }]);
    } catch (err) {
      setError(err.message);
    }
  };

  const chatHistory = useMemo(
    () => messages.filter((msg) => msg.role === "user" || msg.role === "assistant"),
    [messages]
  );

  useEffect(() => {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  useEffect(() => {
    return () => { abortControllerRef.current?.abort(); };
  }, []);

  const onStop = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setBusy(false);
  };

  const onSubmit = async (event, inputRef) => {
    event.preventDefault();
    const cleaned = text.trim();
    if (!cleaned || busy || !currentSessionId) return;

    setError("");
    const userMessage = { id: createMessageId(), role: "user", content: cleaned };
    const assistantMessageId = createMessageId();

    setMessages((prev) => [...prev, userMessage, { id: assistantMessageId, role: "assistant", content: "" }]);
    setText("");
    setBusy(true);
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      await sendMessageStream({
        message: cleaned,
        sessionId: currentSessionId,
        history: chatHistory,
        signal: abortController.signal,
        onDelta: (delta) => {
          setMessages((prev) =>
            prev.map((msg) => msg.id === assistantMessageId ? { ...msg, content: `${msg.content}${delta}` } : msg)
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

      // Actualizar titulo de la sesion actual LOCALMENTE
      setSessions((prev) =>
        prev.map((s) =>
          s.id === currentSessionId && !s.title
            ? { ...s, title: cleaned.length <= 60 ? cleaned : cleaned.slice(0, 57) + "..." }
            : s
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

  if (loadingAuth) {
    return (
      <main className="app-shell">
        <header className="app-header"><div className="brand">ChatLLM Lab</div></header>
        <div className="auth-container"><p style={{ textAlign: "center", color: "var(--muted)" }}>Carregando...</p></div>
      </main>
    );
  }

  if (!user) {
    return <Auth onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand">ChatLLM Lab</div>
        <div className="header-right">
          <span className="user-email">{user}</span>
          <button className="logout-btn" onClick={handleLogout}>Sair</button>
        </div>
      </header>

      <div className="app-layout">
        <Sidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelectSession={handleSelectSession}
          onCreateSession={handleCreateSession}
          userEmail={user}
        />

        <div className="chat-area">
          <section className="messages" aria-live="polite" ref={messagesRef}>
            <div className="messages-inner">
              {messages.map((msg) => (
                <article key={msg.id} className={`bubble ${msg.role}`}>
                  <MessageContent content={msg.content} />
                </article>
              ))}
            </div>
          </section>

          <Composer text={text} busy={busy} error={error} onChangeText={setText} onSubmit={onSubmit} onStop={onStop} />

          <div className="warning-banner">Lembre-se, você precisa focar no experimento!!!</div>
        </div>
      </div>
    </main>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

