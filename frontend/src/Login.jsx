function Login({ onAuthSuccess }) {
  const [mode, setMode] = React.useState("login"); // "login" | "register"
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState("");
  const [busy, setBusy] = React.useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    if (!email.trim() || !password.trim()) {
      setError("Preencha todos os campos.");
      return;
    }
    setBusy(true);
    try {
      const fn = mode === "login" ? apiLogin : apiRegister;
      const data = await fn(email.trim(), password);
      localStorage.setItem("token", data.token);
      localStorage.setItem("email", data.email);
      onAuthSuccess(data.token, data.email);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const switchMode = () => {
    setMode(mode === "login" ? "register" : "login");
    setError("");
  };

  return (
    <main className="app-shell">
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <div className="brand">ChatLLM Lab</div>
            <p className="login-subtitle">
              {mode === "login" ? "Entre com sua conta" : "Crie sua conta"}
            </p>
          </div>

          <form className="login-form" onSubmit={handleSubmit}>
            <div className="login-field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="seu@email.com"
                disabled={busy}
                autoFocus
                autoComplete="email"
              />
            </div>

            <div className="login-field">
              <label htmlFor="password">Senha</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Sua senha"
                disabled={busy}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
              />
            </div>

            {error && <div className="login-error">{error}</div>}

            <button className="login-btn" type="submit" disabled={busy}>
              {busy ? "Aguarde..." : mode === "login" ? "Entrar" : "Criar conta"}
            </button>
          </form>

          <div className="login-footer">
            <span>{mode === "login" ? "Não tem conta?" : "Já tem conta?"}</span>
            <button className="link-btn" onClick={switchMode} disabled={busy}>
              {mode === "login" ? "Criar conta" : "Fazer login"}
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}