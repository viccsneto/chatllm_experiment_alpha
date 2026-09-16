const { useEffect, useMemo, useRef, useState, useCallback } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function generateSessionKey() {
  return `sess_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function App() {
  const [sessions, setSessions] = useState([]);
  const [currentSessionKey, setCurrentSessionKey] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);
  const loadedSessionsRef = useRef({});

  const chatHistory = useMemo(
    () => messages.filter((msg) => msg.role === "user" || msg.role === "assistant"),
    [messages]
  );

  // Carregar sessoes ao montar
  useEffect(() => {
    (async () => {
      try {
        const sess = await listSessions();
        setSessions(sess);
        if (sess.length > 0) {
          setCurrentSessionKey(sess[0].session_key);
        }
      } catch (e) {
        console.error("Erro ao carregar sessoes:", e);
      }
    })();
  }, []);

  // Carregar mensagens ao trocar de sessao
  useEffect(() => {
    if (!currentSessionKey) return;
    if (loadedSessionsRef.current[currentSessionKey]) {
      setMessages(loadedSessionsRef.current[currentSessionKey]);
      return;
    }
    (async () => {
      try {
        const msgs = await getSessionMessages(currentSessionKey);
        const formatted = msgs.map((m) => ({
          id: createMessageId(),
          role: m.role,
          content: m.content,
        }));
        loadedSessionsRef.current[currentSessionKey] = formatted;
        setMessages(formatted);
      } catch (e) {
        console.error("Erro ao carregar mensagens:", e);
        setMessages([]);
      }
    })();
  }, [currentSessionKey]);

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

  const switchSession = useCallback(async (sessionKey) => {
    if (busy) return;
    setCurrentSessionKey(sessionKey);
  }, [busy]);

  const newSession = useCallback(async () => {
    if (busy) return;
    const key = generateSessionKey();
    try {
      await createSession(key);
      const sess = await listSessions();
      setSessions(sess);
      loadedSessionsRef.current[key] = [];
      setCurrentSessionKey(key);
      setMessages([]);
    } catch (e) {
      console.error("Erro ao criar sessao:", e);
    }
  }, [busy]);

  const deleteCurrentSession = useCallback(async () => {
    if (busy || !currentSessionKey) return;
    try {
      await deleteSession(currentSessionKey);
      delete loadedSessionsRef.current[currentSessionKey];
      const sess = await listSessions();
      setSessions(sess);
      if (sess.length > 0) {
        setCurrentSessionKey(sess[0].session_key);
      } else {
        setCurrentSessionKey(null);
        setMessages([]);
      }
    } catch (e) {
      console.error("Erro ao deletar sessao:", e);
    }
  }, [busy, currentSessionKey]);

  const refreshSessions = useCallback(async () => {
    try {
      const sess = await listSessions();
      setSessions(sess);
    } catch (e) {
      console.error("Erro ao atualizar sessoes:", e);
    }
  }, []);

  const onSubmit = async (event, inputRef) => {
    event.preventDefault();
    const cleaned = text.trim();
    if (!cleaned || busy) return;

    // Se nao ha sessao, criar uma
    let key = currentSessionKey;
    if (!key) {
      key = generateSessionKey();
      try {
        await createSession(key);
        loadedSessionsRef.current[key] = [];
        setCurrentSessionKey(key);
      } catch (e) {
        console.error("Erro ao criar sessao:", e);
        return;
      }
    }

    setError("");
    const userMessage = { id: createMessageId(), role: "user", content: cleaned };
    const assistantMessageId = createMessageId();

    const newMessages = [...messages, userMessage, { id: assistantMessageId, role: "assistant", content: "" }];
    loadedSessionsRef.current[key] = newMessages;
    setMessages(newMessages);
    setText("");
    setBusy(true);
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const resultSessionKey = await sendMessageStream({
        message: cleaned,
        history: chatHistory,
        sessionKey: key,
        signal: abortController.signal,
        onDelta: (delta) => {
          setMessages((prev) => {
            const updated = prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: `${msg.content}${delta}` }
                : msg
            );
            loadedSessionsRef.current[key] = updated;
            return updated;
          });
        },
      });

      setMessages((prev) => {
        const updated = prev.map((msg) =>
          msg.id === assistantMessageId && !msg.content.trim()
            ? { ...msg, content: "Nao foi possivel obter resposta do modelo agora." }
            : msg
        );
        loadedSessionsRef.current[key] = updated;
        return updated;
      });

      // Atualizar sessions para pegar o titulo automatico
      await refreshSessions();
    } catch (err) {
      const aborted = err?.name === "AbortError";
      if (!aborted) {
        setError(err.message || "Falha inesperada ao gerar resposta.");
        setMessages((prev) => {
          const updated = prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: msg.content.trim() ? msg.content : "Nao foi possivel obter resposta do modelo agora." }
              : msg
          );
          loadedSessionsRef.current[key] = updated;
          return updated;
        });
      } else {
        setMessages((prev) => {
          const updated = prev.map((msg) =>
            msg.id === assistantMessageId && !msg.content.trim()
              ? { ...msg, content: "Resposta interrompida." }
              : msg
          );
          loadedSessionsRef.current[key] = updated;
          return updated;
        });
      }
    } finally {
      abortControllerRef.current = null;
      setBusy(false);
    }
  };

  return (
    <main className="app-shell">
      <div className={`app-layout ${sidebarOpen ? "sidebar-open" : ""}`}>
        <aside className="sidebar">
          <div className="sidebar-header">
            <button className="new-chat-btn" onClick={newSession} disabled={busy} title="Nova conversa">
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
                key={s.session_key}
                className={`sidebar-item ${s.session_key === currentSessionKey ? "active" : ""}`}
                onClick={() => switchSession(s.session_key)}
              >
                <svg className="sidebar-item-icon" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M8 1C4.1 1 1 3.7 1 7c0 1.9 1 3.6 2.5 4.7L3 15l3.5-2C7.5 13.3 8.7 13.5 10 13c2.8-1 4.5-3.5 4.5-6C14.5 3.7 11.9 1 8 1z" />
                </svg>
                <span className="sidebar-item-title">{s.title || "Nova conversa"}</span>
                {s.session_key === currentSessionKey && (
                  <button
                    className="sidebar-item-delete"
                    onClick={(e) => { e.stopPropagation(); deleteCurrentSession(); }}
                    title="Deletar conversa"
                  >
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                      <line x1="1" y1="1" x2="11" y2="11" />
                      <line x1="11" y1="1" x2="1" y2="11" />
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </div>
        </aside>

        <div className="main-area">
          <header className="app-header">
            <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)} aria-label="Toggle sidebar">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="3" y1="4" x2="15" y2="4" />
                <line x1="3" y1="9" x2="15" y2="9" />
                <line x1="3" y1="14" x2="15" y2="14" />
              </svg>
            </button>
            <div className="brand">ChatLLM Lab</div>
          </header>

          <section className="messages" aria-live="polite" ref={messagesRef}>
            <div className="messages-inner">
              {messages.length === 0 && (
                <div className="empty-state">
                  <p>Inicie uma nova conversa!</p>
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
        </div>
      </div>
    </main>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

