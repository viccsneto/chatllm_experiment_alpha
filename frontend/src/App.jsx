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

  const authAction = authMode === "login" ? window.login : window.signup;

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
    } catch (err) {
      setAuthError(err.message || "Falha ao fazer logout.");
    } finally {
      setAuthBusy(false);
    }
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    const cleaned = text.trim();
    if (!cleaned || busy || authBusy) return;

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
    </main>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

