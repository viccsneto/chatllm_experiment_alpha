const { useEffect, useMemo, useRef, useState } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function ChatApp({ user, onLogout }) {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);
  const titleGeneratedRef = useRef({});
  const sessionIdRef = useRef(null); // Keep latest session ID for callbacks

  // Sync ref with state
  const setSessionId = (id) => {
    sessionIdRef.current = id;
    setCurrentSessionId(id);
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
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  // Load sessions on mount, then restore last active session
  useEffect(() => {
    loadSessionList().then(() => {
      const savedId = localStorage.getItem("current_session_id");
      if (savedId) {
        loadSessionMessages(parseInt(savedId));
      }
    });
  }, []);

  const loadSessionList = async () => {
    try {
      const data = await listSessions();
      setSessions(data.sessions || []);
    } catch {
      // ignore
    }
  };

  const loadSessionMessages = async (sessionId) => {
    try {
      const data = await getSessionMessages(sessionId);
      setMessages(
        data.messages.map((m) => ({
          id: createMessageId(),
          role: m.role,
          content: m.content,
        }))
      );
      setSessionId(sessionId);
      localStorage.setItem("current_session_id", sessionId);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleNewSession = async () => {
    try {
      const session = await createSession(null);
      setSessionId(session.id);
      setMessages([]);
      setError("");
      localStorage.setItem("current_session_id", session.id);
      await loadSessionList();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSelectSession = async (sessionId) => {
    if (busy) return;
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setBusy(false);
    await loadSessionMessages(sessionId);
  };

  const handleDeleteSession = (deletedSessionId) => {
    if (currentSessionId === deletedSessionId) {
      setSessionId(null);
      setMessages([]);
      localStorage.removeItem("current_session_id");
    }
    loadSessionList();
  };

  const generateTitleIfNeeded = async (sid) => {
    if (!sid || titleGeneratedRef.current[sid]) return;
    titleGeneratedRef.current[sid] = true;
    try {
      await generateSessionTitle(sid);
      await loadSessionList();
    } catch {
      // Silently fail
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

    // Capture the session ID at submission time
    const sidAtSubmit = sessionIdRef.current;

    try {
      await sendMessageStream({
        message: cleaned,
        history: chatHistory,
        sessionId: sidAtSubmit,
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
        onSessionId: (newSessionId) => {
          // If this was a new session (no session at submit time), save it
          if (!sidAtSubmit) {
            setSessionId(newSessionId);
            loadSessionList();
            setTimeout(() => generateTitleIfNeeded(newSessionId), 500);
          } else {
            // Existing session — generate title if not yet done
            generateTitleIfNeeded(sidAtSubmit);
          }
        },
      });

      // Generate title for new sessions if onSessionId wasn't called
      if (!sidAtSubmit && sessionIdRef.current) {
        setTimeout(() => generateTitleIfNeeded(sessionIdRef.current), 500);
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
      // Refresh sidebar after message (title may have been generated)
      loadSessionList();
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // Ignore logout errors
    }
    localStorage.removeItem("access_token");
    onLogout();
  };

  return (
    <main className={`app-shell ${sidebarOpen ? "sidebar-visible" : ""}`}>
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        onRenameSession={loadSessionList}
      />

      <div className="chat-area">
        <header className="app-header">
          <div className="header-left">
            <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <line x1="3" y1="4" x2="15" y2="4" />
                <line x1="3" y1="9" x2="15" y2="9" />
                <line x1="3" y1="14" x2="15" y2="14" />
              </svg>
            </button>
            <div className="brand">ChatLLM Lab</div>
          </div>
          <div className="header-right">
            <span className="user-name">{user.name}</span>
            <button className="logout-btn" onClick={handleLogout}>Sair</button>
          </div>
        </header>

        <section className="messages" aria-live="polite" ref={messagesRef}>
          <div className="messages-inner">
            {messages.length === 0 && (
              <div className="empty-chat">
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
    </main>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      getMe()
        .then((userData) => setUser(userData))
        .catch(() => {
          localStorage.removeItem("access_token");
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const handleAuthSuccess = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    setUser(null);
  };

  if (loading) {
    return <main className="app-shell"><div className="loading">Carregando...</div></main>;
  }

  if (!user) {
    return <Auth onAuthSuccess={handleAuthSuccess} />;
  }

  return <ChatApp user={user} onLogout={handleLogout} />;
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

