const { useState } = React;

function Auth({ onAuthSuccess }) {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const fn = mode === "login" ? login : register;
      const result = await fn(email, password);
      localStorage.setItem("chatllm_token", result.token);
      onAuthSuccess(result.email);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setMode(mode === "login" ? "register" : "login");
    setError("");
  };

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand">ChatLLM Lab</div>
      </header>
      <div className="auth-container">
        <form className="auth-form" onSubmit={handleSubmit}>
          <h2>{mode === "login" ? "Entrar" : "Criar Conta"}</h2>

          {error && <div className="note error">{error}</div>}

          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu@email.com"
              required
              autoFocus
            />
          </label>

          <label>
            Senha
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === "login" ? "Sua senha" : "Minimo 6 caracteres"}
              minLength={mode === "register" ? 6 : 1}
              required
            />
          </label>

          <button type="submit" disabled={loading || !email || !password}>
            {loading ? "Aguarde..." : mode === "login" ? "Entrar" : "Cadastrar"}
          </button>

          <p className="auth-toggle">
            {mode === "login" ? (
              <>Nao tem conta? <a href="#" onClick={(e) => { e.preventDefault(); toggleMode(); }}>Cadastre-se</a></>
            ) : (
              <>Ja tem conta? <a href="#" onClick={(e) => { e.preventDefault(); toggleMode(); }}>Entrar</a></>
            )}
          </p>
        </form>
      </div>
    </main>
  );
}