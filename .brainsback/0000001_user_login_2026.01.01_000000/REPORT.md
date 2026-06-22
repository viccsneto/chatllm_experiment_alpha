# Implementation Report

> A concise summary for the reviewer.

**Reviewer note**: If a PR modifies `.brainsback/<task-folder>/TODO.md` or `.brainsback/<task-folder>/REACTO.md`, assume this is expected and that those files were modified by the human developer.
If present, use `.github/skills/brainsback-reviewer/SKILL.md` as the review rubric.

## Snapshot
- **Change**: Implementación de autenticación por email y senha (login/logout/register) con JWT, bcrypt, rate limiting, y proteccion de rutas de chat.
- **Status**: Implementado y funcional (43 tests pasando).

## The Changes

### Backend — Nuevos archivos
- **`backend/schemas/auth.py`** — Schemas Pydantic: `RegisterRequest`, `LoginRequest`, `AuthResponse`, `MeResponse`, `LogoutResponse`.
- **`backend/auth.py`** — Lógica de autenticación: hash con bcrypt, generación/verificación de JWT, rate limiting en memoria (5 intentos, bloqueo 5 min), dependencia `get_current_user()` para proteger rutas.
- **`backend/routers/auth.py`** — Endpoints: `POST /api/register`, `POST /api/login`, `POST /api/logout`, `GET /api/me`.

### Backend — Archivos modificados
- **`backend/models.py`** — Nuevo modelo `User` (tabla `users`) con `id`, `email` (único), `hashed_password`, `is_active`, `created_at`.
- **`backend/config.py`** — Nuevas configs: `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRY_HOURS`, `MAX_LOGIN_ATTEMPTS`, `LOGIN_BLOCK_MINUTES`.
- **`backend/main.py`** — Registrado `auth_router`.
- **`backend/routers/chat.py`** — Endpoints `/api/chat` y `/api/chat/stream` ahora protegidos con `get_current_user`.

### Frontend — Archivos nuevos
- **`frontend/src/Auth.jsx`** — Componente React con formulario de login/register, alternancia entre modos, manejo de errores.

### Frontend — Archivos modificados
- **`frontend/src/api.js`** — Nuevas funciones: `register()`, `login()`, `logout()`, `me()`, helpers `getToken()`, `authHeaders()`. `sendMessageStream()` ahora incluye token en headers.
- **`frontend/src/App.jsx`** — Estado de autenticación: verifica token al cargar, muestra `Auth` si no logueado, botón "Sair" en header si logueado.
- **`frontend/index.html`** — Nuevos estilos para formulario auth, header con email y botón logout. Incluye `Auth.jsx`.

### Tests — Archivos modificados
- **`tests/conftest.py`** — Nuevos fixtures: `test_user` (crea usuario), `auth_headers` (hace login y devuelve headers).
- **`tests/test_chat.py`** — Tests existentes ahora usan `auth_headers`. Nuevos tests: `test_chat_requires_auth`, `test_chat_stream_requires_auth`.

### Dependencias agregadas
- `pyjwt`, `bcrypt`, `email-validator` en `backend/requirements.txt`.

## Core logic
1. **Registro**: Valida email (único) y password (min 6 chars), hashea con bcrypt, guarda en SQLite, devuelve JWT.
2. **Login**: Verifica credenciales, rate limiting (5 intentos → 429 por 5 min), devuelve JWT (expira 24h).
3. **Protección**: `get_current_user()` decodifica JWT, busca usuario en BD, rechaza con 401 si inválido/expirado.
4. **Logout**: Frontend-only (elimina token de localStorage), endpoint confirma token era válido.
5. **Rate limiting**: En memoria (se reinicia al reiniciar servidor), cuenta intentos por email, bloquea tras 5 fallos en ventana de 5 min.

## Testing Strategy
- **43 tests automatizados** con pytest y SQLite en memoria.
- Tests de autenticación cubren: registro, login, login erroneo, email repetido, rutas protegidas sin token.
- Pruebas manuales con curl verificando cada endpoint y casos de error.

## Risks & Follow-up
- [ ] Rate limiting es en memoria → se pierde al reiniciar el servidor. Para produccion usar BD o Redis.
- [ ] Sin refresh tokens — el JWT expira en 24h y hay que hacer login de nuevo.
- [ ] Sin verificación de email — cualquiera puede registrarse con cualquier email.
- [ ] JWT_SECRET debería rotarse periódicamente en producción.

---
**Note**: Usually filled by the AI.
