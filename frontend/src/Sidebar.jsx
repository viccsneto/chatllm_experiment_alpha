function Sidebar({ sessions, activeSessionId, onSelectSession, onCreateSession, onDeleteSession, onToggle, collapsed }) {
  return (
    <div className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-header">
        {!collapsed && <span className="sidebar-title">Conversas</span>}
        <button className="sidebar-toggle-btn" onClick={onToggle} aria-label={collapsed ? "Abrir sidebar" : "Fechar sidebar"}>
          {collapsed ? "☰" : "✕"}
        </button>
      </div>

      {!collapsed && (
        <>
          <button className="new-chat-btn" onClick={onCreateSession}>
            + Nova conversa
          </button>

          <div className="session-list">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`session-item ${session.id === activeSessionId ? "active" : ""}`}
                onClick={() => onSelectSession(session.id)}
              >
                <div className="session-item-content">
                  <span className="session-title">
                    {session.title || "Nova conversa"}
                  </span>
                  <span className="session-date">
                    {new Date(session.updated_at).toLocaleDateString("pt-BR")}
                  </span>
                </div>
                <button
                  className="session-delete-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(session.id);
                  }}
                  aria-label="Excluir conversa"
                  title="Excluir"
                >
                  🗑️
                </button>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}