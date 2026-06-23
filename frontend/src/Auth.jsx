const { useState, useMemo } = React;

const AUTH_STORAGE_KEY = "chatllm_auth";

const EMAIL_RE = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$/;

function getStoredAuth() {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (data && data.email && data.token) return data;
  } catch {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  }
  return null;
}

function setStoredAuth(email, token) {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ email, token }));
}

function clearStoredAuth() {
  localStorage.removeItem(AUTH_STORAGE_KEY);
}

function AuthScreen({ onAuthSuccess }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const emailError = useMemo(() => {
    if (!email) return "";
    if (!EMAIL_RE.test(email)) return "Email invalido.";
    return "";
  }, [email]);

  const canSubmit = email.trim() && !emailError && password.length >= 6;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    setError("");
    setLoading(true);
    try {
      if (mode === "register") {
        await apiRegister(email, password);
        const loginRes = await apiLogin(email, password);
        setStoredAuth(loginRes.email, loginRes.token);
        onAuthSuccess(loginRes.email, loginRes.token);
      } else {
        const res = await apiLogin(email, password);
        setStoredAuth(res.email, res.token);
        onAuthSuccess(res.email, res.token);
      }
    } catch (err) {
      setError(err.message || "Erro inesperado.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <h1 className="auth-title">ChatLLM Lab</h1>
        <p className="auth-subtitle">
          {mode === "login" ? "Entre com sua conta" : "Crie sua conta"}
        </p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          <div className="auth-field">
            <input
              type="email"
              placeholder="Seu email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
              disabled={loading}
              className={emailError ? "input-error" : ""}
            />
            {emailError && <span className="field-error">{emailError}</span>}
          </div>
          <div className="auth-field">
            <input
              type="password"
              placeholder="Sua senha"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              disabled={loading}
            />
          </div>
          <button type="submit" disabled={loading || !canSubmit}>
            {loading
              ? "Aguarde..."
              : mode === "login"
              ? "Entrar"
              : "Cadastrar"}
          </button>
        </form>

        <p className="auth-toggle">
          {mode === "login" ? (
            <>
              Nao tem conta?{" "}
              <a href="#" onClick={(e) => { e.preventDefault(); setMode("register"); setError(""); }}>
                Cadastre-se
              </a>
            </>
          ) : (
            <>
              Ja tem conta?{" "}
              <a href="#" onClick={(e) => { e.preventDefault(); setMode("login"); setError(""); }}>
                Faca login
              </a>
            </>
          )}
        </p>
      </div>
    </div>
  );
}