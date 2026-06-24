const { useState } = React;

function Sidebar({ sessions, activeKey, onSelect, onCreate, onDelete, onToggle, open }) {
  return (
    <div className={`sidebar ${open ? "sidebar--open" : "sidebar--closed"}`}>
      <div className="sidebar-header">
        <button className="sidebar-new-btn" onClick={onCreate}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="7" y1="1" x2="7" y2="13" />
            <line x1="1" y1="7" x2="13" y2="7" />
          </svg>
          Nova conversa
        </button>
        <button className="sidebar-close-btn" onClick={onToggle} aria-label="Fechar sidebar">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="4" y1="4" x2="12" y2="12" />
            <line x1="12" y1="4" x2="4" y2="12" />
          </svg>
        </button>
      </div>

      <div className="sidebar-list">
        {sessions.length === 0 && (
          <div className="sidebar-empty">Nenhuma conversa ainda</div>
        )}
        {sessions.map((s) => (
          <div
            key={s.session_key}
            className={`sidebar-item ${s.session_key === activeKey ? "sidebar-item--active" : ""}`}
            onClick={() => onSelect(s.session_key)}
          >
            <div className="sidebar-item-title">{s.title}</div>
            <button
              className="sidebar-item-delete"
              onClick={(e) => { e.stopPropagation(); onDelete(s.session_key); }}
              aria-label="Deletar conversa"
              title="Deletar"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                <line x1="2" y1="2" x2="10" y2="10" />
                <line x1="10" y1="2" x2="2" y2="10" />
              </svg>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}