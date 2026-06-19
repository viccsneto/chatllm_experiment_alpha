# 🗂️ Tarefa 2 — Sessões de Chat com Título Automático

## 🎯 Objetivo

Implementar um sistema de **sessões de chat** com **barra lateral** e **título automático**, similar ao ChatGPT/Gemini. Cada conversa se torna uma "sessão" separada, com histórico próprio e um título gerado automaticamente.

---

## 🔧 Backend — Python / FastAPI

### 1. Modelo `ChatSession` (SQLAlchemy)

Nova tabela no `backend/models.py`:

| Campo | Tipo | Detalhes |
|-------|------|----------|
| `id` | Integer (PK) | Auto incremento |
| `user_id` | Integer (FK → `users.id`) | Chave estrangeira |
| `title` | String(255) | Pode ser `NULL` (gerado automaticamente depois) |
| `created_at` | DateTime | Preenchido automaticamente |
| `updated_at` | DateTime | Atualizado ao enviar nova mensagem |

### 2. Modelo `ChatMessage` — Adicionar `session_id`

O modelo `ChatMessage` já existe. Vamos **adicionar** o campo:
- `session_id` — Integer (FK → `chat_sessions.id`), permite `NULL` para compatibilidade

### 3. Schemas Pydantic (novo arquivo `backend/schemas/session.py`)

- `SessionCreate` — sem campos (ou `title` opcional)
- `SessionResponse` — `id`, `title` (nullable), `created_at`, `updated_at`
- `SessionListResponse` — lista de `SessionResponse`

### 4. Rotas de Sessão (novo arquivo `backend/routers/sessions.py`)

| Método | Rota | Função |
|--------|------|--------|
| `GET` | `/api/sessions` | Listar sessões do usuário (ordenado por `updated_at` DESC) |
| `POST` | `/api/sessions` | Criar nova sessão (título vazio) |
| `PATCH` | `/api/sessions/{id}` | Atualizar título (usado pelo título automático) |
| `DELETE` | `/api/sessions/{id}` | Excluir sessão e suas mensagens |
| `GET` | `/api/sessions/{id}/messages` | Retornar mensagens de uma sessão específica |

Todas protegidas por `get_current_user`.

### 5. Atualizar `POST /api/chat/stream`

O payload `ChatRequest` deve ganhar um campo opcional:
- `session_id: int | None = None`

**Fluxo:**
- Se `session_id` for fornecido, salva as mensagens **vinculadas à sessão**
- Se `session_id` for `None`, salva como `session_id = NULL` (comportamento atual)
- Após a **primeira mensagem** de uma sessão **sem título**, dispara o título automático

### 6. Título Automático

Estratégia:
1. Após salvar a primeira troca (user + assistant) de uma sessão sem título
2. Fazer uma chamada leve ao OpenRouter com prompt:
   > *"Generate a short title (max 6 words, in the same language as the conversation) for a conversation that starts with this message: {primeira mensagem do usuário}. Return only the title, no quotation marks."*
3. Salvar o título no `ChatSession.title` via `PATCH`

---

## 🎨 Frontend — React

### 1. `frontend/src/Sidebar.jsx` (novo)

Componente de barra lateral:

```
┌─────────────────┬──────────────────────────────┐
│   Sidebar       │                              │
│  ┌───────────┐  │                              │
│  │ + Nova    │  │      Área do Chat            │
│  │ Conversa  │  │                              │
│  └───────────┘  │                              │
│                 │                              │
│  ┌───────────┐  │                              │
│  │ 📄 Título │  │                              │
│  │ 19/06     │  │                              │
│  │ 🗑️       │  │                              │
│  ├───────────┤  │                              │
│  │ 📄 Título │  │                              │
│  │ 19/06     │  │                              │
│  │ 🗑️       │  │                              │
│  └───────────┘  │                              │
└─────────────────┴──────────────────────────────┘
```

**Funcionalidades:**
- Botão **"+ Nova Conversa"** no topo — cria sessão e limpa o chat
- Lista de sessões com título + data formatada
- Sessão ativa destacada (background diferente)
- Clique em uma sessão → carrega suas mensagens via `GET /api/sessions/{id}/messages`
- Ícone de lixeira para excluir sessão (com confirmação)
- Botão colapsável em telas pequenas (hamburger)

### 2. Atualizar `frontend/src/api.js`

Novas funções:
- `apiListSessions()` → `GET /api/sessions`
- `apiCreateSession()` → `POST /api/sessions`
- `apiDeleteSession(id)` → `DELETE /api/sessions/{id}`
- `apiGetSessionMessages(id)` → `GET /api/sessions/{id}/messages`
- Atualizar `sendMessageStream` para aceitar `sessionId` no body

### 3. Atualizar `frontend/src/App.jsx`

**Estado global**:
- `sessions` — lista de sessões
- `activeSessionId` — ID da sessão ativa (`null` = nenhuma)
- `sessionTitles` — mapa de `id → title`

**Fluxo:**
1. Ao carregar (usuário logado), busca `GET /api/sessions`
2. Se não houver sessões, criar uma automaticamente
3. Ao selecionar sessão, carregar mensagens via `GET /api/sessions/{id}/messages`
4. Ao criar nova sessão, limpar chat e definir como ativa
5. Ao enviar mensagem, incluir `session_id` no payload
6. Após receber resposta, atualizar título na sidebar (se mudou)

### 4. Atualizar CSS (`index.html`)

Estilos para:
- Layout de duas colunas (sidebar + chat)
- Sidebar com largura fixa (~260px) em desktop, colapsável em mobile
- Botão de toggle hamburger
- Itens da sidebar com hover, active state, truncate de título
- Botão de excluir com ícone visível apenas no hover

---

## 🧪 Testes

### `tests/test_sessions.py` (novo)

| Teste | Descrição |
|-------|-----------|
| `test_create_session` | Criar sessão retorna 201 com id |
| `test_list_sessions` | Listar retorna apenas sessões do usuário |
| `test_list_sessions_other_user` | Usuário B não vê sessões do usuário A |
| `test_delete_session` | Excluir sessão remove mensagens associadas |
| `test_get_session_messages` | Mensagens da sessão são retornadas |
| `test_session_order` | Sessões ordenadas por `updated_at` DESC |
| `test_unauthorized_access` | Sem token = 401 |

### Atualizar `tests/test_chat.py`

- Testar `POST /api/chat/stream` com `session_id` válido
- Testar `POST /api/chat/stream` com `session_id` inválido (404)

---

---

## 🔁 Observação Importante — Testes Iterativos

**Testes devem ser realizados durante todo o desenvolvimento, não apenas ao final.** A cada alteração significativa (modelo, rota, componente, integração), os testes devem ser executados para validar a mudança. O desenvolvimento será considerado completo **apenas quando todos os testes passarem com sucesso**.

---

## 📦 Resumo de Arquivos

| Arquivo | Ação |
|---------|------|
| `backend/models.py` | ✏️ Adicionar `ChatSession`, adicionar `session_id` em `ChatMessage` |
| `backend/schemas/session.py` | ✏️ Criar schemas de sessão |
| `backend/routers/sessions.py` | ✏️ Criar rotas CRUD de sessões |
| `backend/routers/chat.py` | ✏️ Atualizar para aceitar `session_id` e gerar título |
| `backend/services/openrouter.py` | ✏️ Adicionar função `generate_title` |
| `backend/main.py` | ✏️ Registrar novo router |
| `frontend/src/Sidebar.jsx` | ✏️ Criar componente de barra lateral |
| `frontend/src/api.js` | ✏️ Adicionar funções de sessão |
| `frontend/src/App.jsx` | ✏️ Adicionar estado de sessões e sidebar |
| `frontend/index.html` | ✏️ Adicionar CSS da sidebar, script do Sidebar.jsx |
| `tests/test_sessions.py` | ✏️ Criar testes de sessão |
| `tests/test_chat.py` | ✏️ Atualizar testes com session_id |