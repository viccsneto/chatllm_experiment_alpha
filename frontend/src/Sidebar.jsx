const { useEffect, useRef, useState } = React;

function Sidebar({ sessions, currentSessionId, onSelectSession, onNewSession, onDeleteSession, onRenameSession }) {
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");
  const inputRef = useRef(null);

  useEffect(() => {
    if (editingId) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [editingId]);

  const handleDelete = async (e, sessionId) => {
    e.stopPropagation();
    if (confirm("Deletar esta sessao?")) {
      try {
        await deleteSession(sessionId);
        onDeleteSession(sessionId);
      } catch {
        // ignore
      }
    }
  };

  const startEditing = (e, session) => {
    e.stopPropagation();
    setEditingId(session.id);
    setEditValue(session.title);
  };

  const saveEdit = async () => {
    const id = editingId;
    if (!id) return;
    const newTitle = editValue.trim() || "Nova conversa";
    try {
      await updateSessionTitle(id, newTitle);
      onRenameSession();
    } catch {
      // ignore
    }
    setEditingId(null);
  };

  const handleEditKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      saveEdit();
    } else if (e.key === "Escape") {
      setEditingId(null);
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onNewSession}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden="true">
            <line x1="7" y1="1" x2="7" y2="13" />
            <line x1="1" y1="7" x2="13" y2="7" />
          </svg>
          Novo chat
        </button>
      </div>
      <div className="sidebar-list">
        {sessions.length === 0 && (
          <div className="sidebar-empty">Nenhuma conversa ainda</div>
        )}
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`sidebar-item ${s.id === currentSessionId ? "active" : ""}`}
            onClick={() => onSelectSession(s.id)}
          >
            {editingId === s.id ? (
              <input
                ref={inputRef}
                className="sidebar-edit-input"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onBlur={saveEdit}
                onKeyDown={handleEditKeyDown}
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              <>
                <span className="sidebar-item-title">{s.title}</span>
                <button
                  className="sidebar-item-edit"
                  onClick={(e) => startEditing(e, s)}
                  title="Renomear"
                >
                  <svg width="11" height="11" viewBox="0 0 11 11" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
                    <path d="M1 8.5V10H2.5L8.5 4L7 2.5L1 8.5Z" />
                    <line x1="7" y1="4" x2="8.5" y2="2.5" />
                  </svg>
                </button>
                <button
                  className="sidebar-item-delete"
                  onClick={(e) => handleDelete(e, s.id)}
                  title="Deletar sessao"
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
                    <line x1="2" y1="2" x2="10" y2="10" />
                    <line x1="10" y1="2" x2="2" y2="10" />
                  </svg>
                </button>
              </>
            )}
          </div>
        ))}
      </div>
    </aside>
  );
}