const { useState } = React;

function Auth({ onAuthSuccess }) {
  const [mode, setMode] = useState("login"); // login | signup | forgot | verify | reset
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    new_password: "",
    security_question: "",
    security_answer: "",
  });
  const [securityQuestion, setSecurityQuestion] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSignup = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await signup(form);
      localStorage.setItem("access_token", data.access_token);
      onAuthSuccess(data.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login({ email: form.email, password: form.password });
      localStorage.setItem("access_token", data.access_token);
      onAuthSuccess(data.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await forgotPassword({ email: form.email });
      setSecurityQuestion(data.security_question);
      setSuccess("Pergunta de seguranca carregada. Responda para redefinir a senha.");
      setMode("verify");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyAnswer = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await verifySecurityAnswer({ email: form.email, security_answer: form.security_answer });
      setSuccess("Resposta correta! Defina sua nova senha.");
      setMode("reset");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await resetPassword({ email: form.email, new_password: form.new_password });
      setSuccess("Senha redefinida com sucesso! Faca login.");
      setMode("login");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const showLogin = () => { setMode("login"); setError(""); setSuccess(""); };
  const showSignup = () => { setMode("signup"); setError(""); setSuccess(""); };
  const showForgot = () => { setMode("forgot"); setError(""); setSuccess(""); };

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand">ChatLLM Lab</div>
      </header>

      <div className="auth-container">
        <div className="auth-card">
          {mode === "login" && (
            <>
              <h2>Entrar</h2>
              {error && <div className="auth-error">{error}</div>}
              {success && <div className="auth-success">{success}</div>}
              <form onSubmit={handleLogin}>
                <input value={form.email} onChange={update("email")} placeholder="Email" type="email" required />
                <input value={form.password} onChange={update("password")} placeholder="Senha" type="password" required />
                <button type="submit" disabled={loading}>{loading ? "Entrando..." : "Entrar"}</button>
              </form>
              <div className="auth-links">
                <button className="link-btn" onClick={showSignup}>Criar conta</button>
                <button className="link-btn" onClick={showForgot}>Esqueci a senha</button>
              </div>
            </>
          )}

          {mode === "signup" && (
            <>
              <h2>Criar Conta</h2>
              {error && <div className="auth-error">{error}</div>}
              <form onSubmit={handleSignup}>
                <input value={form.name} onChange={update("name")} placeholder="Nome" required />
                <input value={form.email} onChange={update("email")} placeholder="Email" type="email" required />
                <input value={form.password} onChange={update("password")} placeholder="Senha (min. 6 caracteres)" type="password" required minLength={6} />
                <div className="field-help">
                  <input value={form.security_question} onChange={update("security_question")} placeholder="Pergunta de seguranca" required />
                  <span className="field-hint">Crie uma pergunta cuja resposta voce lembre facilmente. Sera usada para recuperar sua senha.</span>
                </div>
                <input value={form.security_answer} onChange={update("security_answer")} placeholder="Resposta da pergunta de seguranca" required />
                <button type="submit" disabled={loading}>{loading ? "Criando..." : "Criar conta"}</button>
              </form>
              <div className="auth-links">
                <button className="link-btn" onClick={showLogin}>Ja tenho conta</button>
              </div>
            </>
          )}

          {mode === "forgot" && (
            <>
              <h2>Recuperar Senha</h2>
              {error && <div className="auth-error">{error}</div>}
              <form onSubmit={handleForgotPassword}>
                <input value={form.email} onChange={update("email")} placeholder="Email" type="email" required />
                <button type="submit" disabled={loading}>{loading ? "Buscando..." : "Buscar pergunta"}</button>
              </form>
              <div className="auth-links">
                <button className="link-btn" onClick={showLogin}>Voltar ao login</button>
              </div>
            </>
          )}

          {mode === "verify" && (
            <>
              <h2>Pergunta de Seguranca</h2>
              {error && <div className="auth-error">{error}</div>}
              {success && <div className="auth-success">{success}</div>}
              <p className="security-question"><strong>{securityQuestion}</strong></p>
              <form onSubmit={handleVerifyAnswer}>
                <input value={form.security_answer} onChange={update("security_answer")} placeholder="Sua resposta" required />
                <button type="submit" disabled={loading}>{loading ? "Verificando..." : "Verificar resposta"}</button>
              </form>
              <div className="auth-links">
                <button className="link-btn" onClick={showLogin}>Voltar ao login</button>
              </div>
            </>
          )}

          {mode === "reset" && (
            <>
              <h2>Redefinir Senha</h2>
              {error && <div className="auth-error">{error}</div>}
              {success && <div className="auth-success">{success}</div>}
              <form onSubmit={handleResetPassword}>
                <input value={form.new_password} onChange={update("new_password")} placeholder="Nova senha (min. 6 caracteres)" type="password" required minLength={6} />
                <button type="submit" disabled={loading}>{loading ? "Redefinindo..." : "Redefinir senha"}</button>
              </form>
              <div className="auth-links">
                <button className="link-btn" onClick={showLogin}>Voltar ao login</button>
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}