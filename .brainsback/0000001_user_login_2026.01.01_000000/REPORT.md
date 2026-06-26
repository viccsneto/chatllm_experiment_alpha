# Implementation Report

> A concise summary for the reviewer.

**Reviewer note**: If a PR modifies `.brainsback/<task-folder>/TODO.md` or `.brainsback/<task-folder>/REACTO.md`, assume this is expected and that those files were modified by the human developer.
If present, use `.github/skills/brainsback-reviewer/SKILL.md` as the review rubric.

## Snapshot
- **Change**: Implementação de autenticação (login/logout) com email e senha, persistência em SQLite, device fingerprint, e HMAC com suporte a múltiplas chaves.
- **Status**: Completo. 77/77 testes passando.

## The Changes

### Backend - Modelos (`backend/models.py`)
- **`User`**: tabela `users` com `email` (unique), `password_hash` (formato `key_id:hash`), `created_at`
- **`DeviceSession`**: tabela `device_sessions` com `email`, `device_fingerprint`, `token` (UUID), `logged_in`, `expires_at` (7 dias)
- **`HashingKey`**: tabela `hashing_keys` com `key_id` (prefixo), `key_value`, `active`, para suporte a rotação de chaves

### Backend - Schemas (`backend/schemas/auth.py`)
- `RegisterRequest` / `RegisterResponse`: email (EmailStr) + password
- `LoginRequest` / `LoginResponse`: email + password + device_fingerprint → token
- `LogoutRequest` / `LogoutResponse`: email + token
- `MeResponse`: email (via token validation)

### Backend - Serviço (`backend/services/auth.py`)
- **HMAC-SHA256**: `hmac(key, email + password)` com segredo do servidor
- **Múltiplas chaves**: `HashingKey` ativa é usada para novos hashes; chaves antigas continuam funcionando para verificação
- **Timing-safe comparison**: `hmac.compare_digest()` — o Python já garante tempo constante independente dos valores ou comprimentos, então não há necessidade de verificação prévia de tamanho nem chamadas duplas
- **Token UUID**: gerado no login, expira em 7 dias
- **Funções**: `register_user`, `login_user`, `logout_user`, `get_logged_in_email`

### Backend - Router (`backend/routers/auth.py`)
- `POST /auth/register` → 201 (cadastro) ou 409 (duplicado)
- `POST /auth/login` → 200 (token) ou 401 (credenciais inválidas)
- `POST /auth/logout` → 200 ou 404 (sessão não encontrada)
- `GET /auth/me` → 200 (email) ou 401 (token inválido/expirado)

### Backend - Config (`backend/config.py`)
- Adicionado `SERVER_SECRET_HASH` (lido do `.env`, default para dev)

### Backend - Main (`backend/main.py`)
- Router `auth_router` registrado na aplicação

### Frontend (`frontend/`)
- **`api.js`**: `getDeviceFingerprint()` (userAgent + screen + canvas + language + etc.), `apiRegister`, `apiLogin`, `apiLogout`, `apiMe`
- **`Auth.jsx`**: Tela de login/cadastro com toggle, armazenamento seguro no localStorage (`email + token` apenas)
- **`App.jsx`**: Render condicional — se não autenticado mostra `AuthScreen`, se autenticado mostra o chat com botão "Sair" e email no header
- **`index.html`**: Estilos CSS para auth screen, header com email e logout

### Dependências
- `pydantic[email]` adicionado ao `requirements.txt`

## Testing Strategy
- **Testes unitários do serviço** (`test_auth_service.py`): 16 testes — `_ensure_active_key`, `_compute_hash`, `_time_safe_equal`, `_verify_hash`, `register_user`, `login_user`, `logout_user`, `get_logged_in_email`
- **Testes de schemas** (`test_auth_schemas.py`): 10 testes — validação de email, password, device_fingerprint
- **Testes de integração router** (`test_auth_router.py`): 4 testes — fluxo completo register → login → me → logout, senha errada, sem token, token inválido
- **77/77 testes passando** (incluindo testes pré-existentes intactos)

## Risks & Follow-up
- [ ] O segredo `SERVER_SECRET_HASH` no `.env` deve ser alterado para um valor seguro em produção
- [ ] Em produção, considerar usar HTTPS para evitar interceptação de tokens
- [ ] O device fingerprint é determinístico no browser — um invasor com mesmo browser/resolução poderia gerar fingerprint idêntico; o token UUID mitiga esse risco
- [ ] Rotações futuras de chave: adicionar nova chave ativa em `hashing_keys` e marcar a anterior como inativa
