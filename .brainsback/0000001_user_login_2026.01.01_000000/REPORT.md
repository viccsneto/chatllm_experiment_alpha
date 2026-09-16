# Relatório de Implementação

> Resumo conciso para o revisor.

## Snapshot
- **Mudança**: Sistema de autenticação de usuários (register, login, logout) com JWT e bcrypt
- **Status**: Completo — 60 testes passando (19 novos testes de auth + 41 existentes)

## Arquivos modificados/criados

### Modificados
- `backend/models.py` — Adicionado modelo `User` (id, email, password_hash, is_active, created_at)
- `backend/config.py` — Adicionadas configs `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `backend/main.py` — Registrado `auth_router` no app FastAPI
- `backend/requirements.txt` — Adicionadas dependências `python-jose[cryptography]` e `bcrypt`

### Criados
- `backend/schemas/auth.py` — Schemas Pydantic: `RegisterRequest`, `LoginRequest`, `AuthResponse`, `UserResponse`
- `backend/services/security.py` — Utilitários: `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`, `get_current_user`
- `backend/routers/auth.py` — Rotas: `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`
- `tests/test_auth.py` — 19 testes cobrindo schemas, endpoints, fluxos de sucesso e erro

## Lógica central

1. **Hash de senha**: `bcrypt.hashpw` com salt gerado automaticamente — senha nunca armazenada em texto plano
2. **JWT**: Tokens criados com `python-jose` (algoritmo HS256), contendo `sub` (user_id) e `email`, expiração em 60 minutos
3. **Proteção de rotas**: `get_current_user` como dependência FastAPI — decodifica token Bearer, busca usuário no banco, retorna 401 se inválido/expirado/inativo
4. **Segurança**: Login retorna "Credenciais inválidas" genérico (não revela se e-mail ou senha está errado); e-mail duplicado retorna 409; prepared statements via SQLAlchemy previnem SQL injection

## Testes
- Schemas: validação de formato de e-mail, tamanho de senha, campos obrigatórios
- Register: sucesso (201), duplicado (409), e-mail inválido (422), senha curta (422)
- Login: sucesso (200), senha errada (401), e-mail inexistente (401)
- Me: autenticado (200), não autenticado (403), token inválido (401)
- Logout: autenticado (200), não autenticado (403)

## Riscos e acompanhamento
- [ ] `SECRET_KEY` no `config.py` tem valor default inseguro (`change-me-to-a-secure-random-string-in-production`) — deve ser configurada via `.env` em produção
- [ ] Token JWT é stateless (sem blacklist) — logout apenas remove o token do lado do cliente; para revogação real seria necessário uma blacklist ou refresh tokens
- [ ] `bcrypt` limita senhas a 72 bytes — aceitável para uso geral, mas bom documentar
