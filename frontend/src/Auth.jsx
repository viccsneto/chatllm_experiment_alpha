const { useState } = React;

function Auth({ mode, onSuccess, onCancel }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const isLogin = mode === "login";

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!email.trim() || !password.trim()) {
      setError("Preencha todos os campos");
      return;
    }

    setLoading(true);
    try {
      const endpoint = isLogin ? "/api/auth/login" : "/api/auth/register";
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || "Erro ao processar requisicao");
        return;
      }

      if (isLogin) {
        setSuccess("Login realizado com sucesso!");
      } else {
        setSuccess("Conta criada com sucesso!");
      }

      setTimeout(() => onSuccess(data), 800);
    } catch (err) {
      setError("Erro de conexao com o servidor");
    } finally {
      setLoading(false);
    }
  };

  const switchMode = isLogin ? "register" : "login";
  const switchLabel = isLogin ? "Criar conta" : "Ja tenho conta";

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2 className="auth-title">{isLogin ? "Login" : "Criar Conta"}</h2>

        {error && <div className="auth-error">{error}</div>}
        {success && <div className="auth-success">{success}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <label className="auth-label">
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu@email.com"
              className="auth-input"
              disabled={loading}
              autoFocus
            />
          </label>

          <label className="auth-label">
            Senha
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={isLogin ? "Sua senha" : "Minimo 6 caracteres"}
              className="auth-input"
              disabled={loading}
              minLength={isLogin ? 1 : 6}
            />
          </label>

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? "Aguarde..." : isLogin ? "Entrar" : "Cadastrar"}
          </button>
        </form>

        <div className="auth-footer">
          <button className="auth-switch" onClick={() => onCancel(switchMode)}>
            {switchLabel}
          </button>
          <button className="auth-cancel" onClick={() => onCancel(null)}>
            Voltar ao chat
          </button>
        </div>
      </div>
    </div>
  );
}