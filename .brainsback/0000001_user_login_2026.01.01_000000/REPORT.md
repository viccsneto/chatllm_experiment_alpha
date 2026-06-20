# Implementation Report

> A concise summary for the reviewer.

**Reviewer note**: If a PR modifies `.brainsback/<task-folder>/TODO.md` or `.brainsback/<task-folder>/REACTO.md`, assume this is expected and that those files were modified by the human developer.
If present, use `.github/skills/brainsback-reviewer/SKILL.md` as the review rubric.

## Snapshot
- **Change**: Implementação de sistema completo de login/logout com cadastro, autenticação JWT, recuperação de senha via pergunta de segurança, e proteção dos endpoints de chat.
- **Status**: Concluído — 54/54 testes passando.

## The Changes
### Backend — Modelos
- `backend/models.py`: Adicionada tabela `User` com campos `name`, `email` (unique), `hashed_password`, `security_question`, `hashed_security_answer`, `created_at`. Adicionado `user_id` opcional em `ChatMessage` para associar mensagens ao usuário.

### Backend — Schemas
- `backend/schemas/auth.py` (novo): Schemas para signup, login, forgot-password, verify-security-answer, reset-password, auth response, security question response, message response.

### Backend — Rotas de Autenticação
- `backend/routers/auth.py` (novo): Endpoints em `/api/auth/`:
  - `POST /signup` — cadastro com hash bcrypt de senha e resposta de segurança
  - `POST /login` — login com validação de senha, retorna JWT
  - `POST /forgot-password` — retorna pergunta de segurança do email
  - `POST /verify-security-answer` — valida resposta de segurança
  - `POST /reset-password` — redefine senha
  - `POST /logout` — logout (stateless, apenas confirmação)

### Backend — Proteção do Chat
- `backend/routers/chat.py`: Adicionada dependência `get_current_user` que extrai e valida JWT do header `Authorization: Bearer <token>`. Todos os endpoints `/api/chat` e `/api/chat/stream` agora exigem autenticação (401 se ausente/inválido). Adicionado `GET /api/auth/me` para verificar sessão atual. Mensagens do chat agora associadas ao `user_id`.

### Backend — Config
- `backend/config.py`: Adicionadas variáveis `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`.

### Backend — Dependências
- `backend/requirements.txt`: Adicionados `passlib[bcrypt]` e `python-jose[cryptography]`.

### Frontend — API
- `frontend/src/api.js`: Adicionadas funções `signup`, `login`, `forgotPassword`, `verifySecurityAnswer`, `resetPassword`, `logout`, `getMe`. Todas as chamadas de chat agora incluem `Authorization` header com token do `localStorage`.

### Frontend — Componente de Auth
- `frontend/src/Auth.jsx` (novo): Componente React com fluxos de: login, cadastro, recuperação de senha (pergunta de segurança → verificar resposta → redefinir senha). Armazena token no `localStorage`.

### Frontend — App.jsx
- `frontend/src/App.jsx`: Reestruturado para gerenciar estado de autenticação. `App` principal verifica token existente via `getMe()`. Se não autenticado, renderiza `<Auth />`. Se autenticado, renderiza `<ChatApp />` com nome do usuário e botão de logout no header.

### Frontend — HTML/CSS
- `frontend/index.html`: Adicionados estilos para auth card, formulários, mensagens de erro/sucesso, botão de logout, header com flexbox. Incluído script `Auth.jsx`.

### Testes
- `tests/test_auth.py` (novo): 11 testes cobrindo signup (sucesso, duplicata, dados inválidos), login (sucesso, senha errada, email inexistente), forgot-password (fluxo completo, email inexistente), logout, `/api/auth/me` (autenticado e não autenticado).
- `tests/test_chat.py`: Atualizado — todos os endpoints de chat agora testam que exigem token 401. Adicionado helper `get_token()` para gerar token nos testes.

## Testing Strategy
- Suite completa de 54 testes pytest com banco SQLite em memória.
- Cobertura de auth: cadastro, login, duplicata, recuperação de senha (4 etapas), logout, verificação de sessão.
- Cobertura de chat: endpoints protegidos retornam 401 sem token, fluxo existente mantido.
- CORS e health endpoint permanecem públicos.

### Frontend — Melhorias de UX
- `frontend/src/api.js`: `apiPost` e `apiGet` agora tratam respostas não-JSON (ex: HTML de erro 500) com mensagem amigável ao invés de "Unexpected token". Mensagem de erro no `sendMessageStream` inclui "Verifique se voce esta logado."
- `frontend/src/Auth.jsx`: Adicionada explicação visual no campo "Pergunta de segurança" com hint sobre recuperação de senha.
- `frontend/index.html`: Adicionados estilos `.field-help` e `.field-hint`.

## Risks & Follow-up
- [ ] `JWT_SECRET_KEY` está configurada com valor default `super-secret-key-mude-em-producao` — idealmente deve ser uma variável de ambiente secreta.
- [ ] Token JWT expira em 24h — não há refresh token implementado.
- [ ] Senha com limite de 128 caracteres — bcrypt trunca em 72 bytes.
- [ ] Logout é stateless (apenas remove token no frontend) — sem blacklist de tokens.

---
**Note**: Usually filled by the AI.
