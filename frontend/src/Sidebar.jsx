const { useState } = React;

function Sidebar({ sessions, activeSessionId, onSelectSession, onCreateSession, onDeleteSession, onClose }) {
  return (
    <div className="sidebar-overlay" onClick={onClose}>
      <aside className="sidebar" onClick={(e) => e.stopPropagation()}>
        <div className="sidebar-header">
          <h3>Sessoes</h3>
          <button className="sidebar-close-btn" onClick={onClose} aria-label="Fechar sidebar">&times;</button>
        </div>

        <button className="sidebar-new-btn" onClick={onCreateSession}>
          + Nova sessao
        </button>

        <div className="sidebar-list">
          {sessions.length === 0 && (
            <p className="sidebar-empty">Nenhuma sessao ainda</p>
          )}
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`sidebar-item ${s.id === activeSessionId ? "active" : ""}`}
              onClick={() => onSelectSession(s.id)}
            >
              <span className="sidebar-item-title">{s.title || "Nova sessao"}</span>
              <button
                className="sidebar-item-del"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(s.id);
                }}
                aria-label="Remover sessao"
                title="Remover"
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}