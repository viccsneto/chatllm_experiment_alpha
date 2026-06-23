const { useEffect, useMemo, useRef, useState } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
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
      await sendMessageStream({
        message: cleaned,
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
    setMessages([
      {
        id: createMessageId(),
        role: "assistant",
        content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?",
      },
    ]);
  };

  if (!auth) {
    return <AuthPage onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <main className="app-shell">
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
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

