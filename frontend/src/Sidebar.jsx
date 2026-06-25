const { useEffect, useState } = React;

function Sidebar({ activeSessionId, onSelectSession, onNewSession, onDeleteSession }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const data = await listSessions();
      setSessions(data.sessions || []);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, [activeSessionId]);

  const handleDelete = async (e, sessionId) => {
    e.stopPropagation();
    try {
      await deleteSession(sessionId);
      if (activeSessionId === sessionId) {
        onSelectSession(null);
      }
      loadSessions();
    } catch {
      // silently fail
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-title">Sessoes</span>
        <button className="sidebar-new-btn" onClick={onNewSession} title="Nova sessao">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <line x1="7" y1="1" x2="7" y2="13" />
            <line x1="1" y1="7" x2="13" y2="7" />
          </svg>
        </button>
      </div>

      <div className="sidebar-list">
        {loading && sessions.length === 0 && (
          <div className="sidebar-empty">Carregando...</div>
        )}
        {!loading && sessions.length === 0 && (
          <div className="sidebar-empty">Nenhuma sessao</div>
        )}
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`sidebar-item ${s.id === activeSessionId ? "active" : ""}`}
            onClick={() => onSelectSession(s.id)}
          >
            <span className="sidebar-item-title">{s.title}</span>
            <button
              className="sidebar-item-del"
              onClick={(e) => handleDelete(e, s.id)}
              title="Excluir sessao"
            >
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="1" y1="1" x2="9" y2="9" />
                <line x1="9" y1="1" x2="1" y2="9" />
              </svg>
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}