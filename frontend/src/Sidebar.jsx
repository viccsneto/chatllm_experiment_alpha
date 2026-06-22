function Sidebar({ sessions, currentSessionId, onSelectSession, onCreateSession, userEmail }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-user">{userEmail}</span>
      </div>
      <button className="sidebar-new-btn" onClick={onCreateSession}>
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <line x1="7" y1="1" x2="7" y2="13" />
          <line x1="1" y1="7" x2="13" y2="7" />
        </svg>
        Nova conversa
      </button>
      <nav className="sidebar-list">
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`sidebar-item ${s.id === currentSessionId ? "active" : ""}`}
            onClick={() => onSelectSession(s.id)}
          >
            <span className="sidebar-item-title">{s.title || "Sem titulo"}</span>
          </div>
        ))}
        {sessions.length === 0 && (
          <p className="sidebar-empty">Nenhuma conversa ainda.</p>
        )}
      </nav>
    </aside>
  );
}