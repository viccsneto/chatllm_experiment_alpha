# Proof of Mastery (REACTO)

> Explain it to prove you own it.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## R — Repeat (The Problem)
O problema consiste em implementar um sistema de gerenciamento de identidade (cadastro, login e logout) baseado em e-mail e senha, com persistência segura de dados no banco (SQLite). O objetivo é garantir que as senhas não sejam expostas, que as sessões de usuários sejam geridas de forma confiável para proteger rotas privadas da aplicação, e que vulnerabilidades comuns (como enumeração de usuários ou injeção de SQL) sejam mitigadas. 

## E — Examples

- **Happy Path Input (Register)**: `POST /api/auth/register` com payload `{"email": "joao@example.com", "password": "senha_segura"}`
  **Output**: `201 Created` retornando um JSON com `{"access_token": "eyJhbG...", "token_type": "bearer", "email": "joao@example.com"}`.

- **Happy Path Input (Login)**: `POST /api/auth/login` com payload `{"email": "joao@example.com", "password": "senha_segura"}`
  **Output**: `200 OK` retornando o token JWT.

- **Edge Case Input (E-mail duplicado)**: `POST /api/auth/register` usando um e-mail que já existe no SQLite.
  **Output**: `409 Conflict` com a mensagem `{"detail": "Este e-mail ja esta cadastrado."}`.

- **Edge Case Input (Senha Incorreta)**: `POST /api/auth/login` com senha incorreta.
  **Output**: `401 Unauthorized` com a mensagem genérica `{"detail": "Credenciais invalidas."}`.

## A — Approach
A estratégia adotada foi baseada no ecossistema padrão e seguro do FastAPI:
1. **Persistência e Modelagem**: Criação de um modelo `User` via SQLAlchemy (ORM) com restrição de unicidade (`unique=True`) e indexação no e-mail para buscas rápidas.
2. **Segurança de Credenciais**: Utilização da biblioteca `bcrypt` para gerar um *salt* automático e realizar o hash da senha antes de salvá-la, garantindo que o banco de dados armazene apenas o hash irreversível.
3. **Gestão de Sessão**: Adoção de **JWT (JSON Web Tokens)** utilizando a biblioteca `python-jose` (algoritmo HS256). O JWT encapsula a identidade do usuário (ID e e-mail) de forma assinada e com expiração (60 minutos).
4. **Proteção de Rotas**: Implementação de uma dependência FastAPI (`get_current_user`) que valida o `HTTPBearer` token, extrai o usuário e impede o acesso caso o token seja inválido, expirado, ou o usuário esteja inativo.

## C — Code

As adições mais críticas para a segurança e arquitetura foram:

**1. `backend/models.py` - O Modelo de Usuário**
```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```
> **Justificativa**: A coluna `email` recebeu `unique=True` (garante consistência no banco) e `index=True` (acelera o login). A senha é armazenada estritamente como `password_hash`. O campo `is_active` previne que contas suspensas façam login ou acessem a API mesmo com um token ainda não expirado.

**2. `backend/services/security.py` - Hashing e Validação**
```python
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
```
> **Justificativa**: A escolha do `bcrypt` isola a aplicação de ataques de dicionário ou *rainbow tables* através da geração nativa de *salts* criptográficos embutidos no próprio hash final.

**3. `backend/routers/auth.py` - Mensagens Genéricas no Login**
```python
if not user or not verify_password(payload.password, user.password_hash):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais invalidas.",
    )
```
> **Justificativa**: Retornar "Credenciais inválidas" em vez de apontar se foi o e-mail ou a senha que falhou é uma prática fundamental para evitar ataques de Enumeração de Usuários (User Enumeration).

## T — Tests
A solução conta com **19 testes automatizados** focados em autenticação no arquivo `tests/test_auth.py`, utilizando `pytest` e `TestClient` do FastAPI:
- **Testes Unitários (Schemas)**: Cobrem o comportamento do Pydantic em `schemas/auth.py`, garantindo rejeição imediata (HTTP 422) de formatos de e-mail inválidos, senhas muito curtas ou campos vazios.
- **Testes de Integração (Endpoints)**: Simulando o fluxo do cliente:
  - `TestRegisterEndpoint` valida criação (201) e conflitos (409).
  - `TestLoginEndpoint` valida sucesso e, fundamentalmente, assegura o retorno 401 genérico para evitar vazamento de informações.
  - `TestMeEndpoint` e `TestLogoutEndpoint` asseguram que apenas portadores de um token `Bearer` válido recebam status 200, retornando 403 ou 401 caso contrário.

## O — Optimize
- **Complexidade de Tempo (Big O)**:
  - *Busca de Login/Cadastro*: O banco utiliza indexação na coluna de email. A busca do usuário é **O(log N)** (usando B-Trees no SQLite).
  - *Hashing*: **O(N)** intencionalmente lento, onde N é o custo de processamento (*work factor*) configurado pelo bcrypt, planejado como defesa (trade-off de performance por segurança contra força bruta).
- **Trade-offs Atuais**: 
  - *Stateless JWT vs. Logout*: A decisão de usar JWT sem persistência da sessão no backend significa que o endpoint `/logout` não revoga, de fato, o token do lado do servidor (ele apenas confia que o frontend excluirá o token). 
- **Melhorias Futuras (Oportunidades)**:
  - Implementar uma **Blacklist de Tokens** (ex: usando Redis) ou uma arquitetura baseada em **Refresh Tokens** de curta duração para permitir a revogação real de acessos durante o logout.
  - No arquivo `backend/config.py`, o `SECRET_KEY` possui um valor default de *fallback* configurado no código. Em produção, será mandatório assegurar que a aplicação pare sua inicialização (*fail-fast*) se a chave não estiver configurada no `.env`, para evitar assinaturas JWT fáceis de quebrar.
