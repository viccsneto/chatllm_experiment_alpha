# Proof of Mastery (REACTO)

> Explain it to prove you own it.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## R — Repeat (The Problem)
Eu precisava implementar cadastro, login e logout usando email e senha, com os
dados persistidos no SQLite (sobrevivendo a um restart do backend) e com a senha
armazenada de forma segura (nunca em texto puro). O logout precisava realmente
invalidar o acesso, não só esconder um botão no frontend.

## E — Examples

- **Happy Path Input**: POST `/api/auth/signup` com `{email: "ana@teste.com", password: "senha123"}`
  **Output**: 201, usuário criado no banco com senha em hash (bcrypt), retorna um token.

- **Happy Path Input**: POST `/api/auth/login` com email e senha corretos
  **Output**: 200, gera um novo token e salva na tabela `sessions` com expiração de 7 dias.

- **Edge Case Input**: POST `/api/auth/signup` com um email que já existe
  **Output**: 409 (conflito) — não deixa criar duplicado.

- **Edge Case Input**: GET `/api/auth/me` sem token no header
  **Output**: 401.

- **Edge Case Input**: POST `/api/auth/logout` e depois tentar acessar `/api/auth/me` de novo com o mesmo token
  **Output**: 401 — o token foi apagado da tabela `sessions`, então deixa de ser válido na hora.

## A — Approach
A ideia foi: usuário e senha ficam guardados numa tabela `User` (com a senha
já em hash, nunca em texto puro), e cada login cria um registro numa tabela
`Session` separada, com um token aleatório e uma data de expiração. Pra saber
se alguém está logado, o backend olha se existe uma sessão válida com aquele
token. Fazer logout é simplesmente apagar essa sessão do banco — assim o token
para de funcionar imediatamente, mesmo que o frontend ainda "lembre" dele.

Isso é diferente de JWT puro (onde o token se auto-valida sem consultar o
banco): aqui, cada requisição confere no banco se a sessão ainda existe, o que
deixa o logout mais confiável, mas também depende do banco pra validar toda
requisição autenticada.

**Ponto que preciso entender melhor**: eu tinha pensado em usar cookie de
sessão, mas saiu implementado com token guardado no `localStorage` do
navegador e mandado no header `Authorization`. Preciso perguntar/entender por
que isso foi feito assim e se isso é um problema (tipo, exposição a XSS),
porque não foi bem o que eu tinha decidido antes.

## C — Code
- `backend/models.py`: criei (o agente criou) duas tabelas — `User` (id, email,
  hashed_password, created_at) e `Session` (id, token, user_id, created_at,
  expires_at), ligadas por relacionamento. Separar em duas tabelas faz sentido
  porque um usuário pode ter várias sessões ativas (ex: logado em mais de um
  lugar), e dá pra derrubar sessões individualmente sem mexer no usuário.

- `backend/routers/auth.py`: as quatro rotas (`signup`, `login`, `logout`,
  `me`). O hash da senha usa `bcrypt` direto (não `passlib`, porque a versão
  5.0 do bcrypt não é compatível com o passlib — isso eu não sabia e preciso
  entender melhor o motivo técnico).

- `get_current_user()` / `require_user()`: duas dependências do FastAPI, uma
  opcional e outra que já barra com 401 se não tiver usuário. Faz sentido
  separar assim porque nem toda rota precisa exigir login.

## T — Tests
Ficaram 12 testes novos em `tests/test_auth.py`, cobrindo os casos de sucesso
e os principais casos de erro (senha errada, email duplicado, token inválido,
sessão já expirada pelo logout). No total, 32 testes passaram. Duas coisas que
não são falha da minha implementação:
- um teste pré-existente do chat que já falhava antes (não relacionado a auth);
- um teste de validação de email que precisou ser ajustado porque o schema
  atual só confere o tamanho da string, não se é um email de verdade.

Ainda preciso confirmar manualmente (não só confiar no relatório) que reiniciar
o backend não apaga os usuários — isso está marcado como validado no relatório,
mas quero testar com minhas próprias mãos antes de aceitar.

## O — Optimize
- A validação de email só olha o tamanho (5+ caracteres), não o formato. Pra
  produção isso deveria usar `pydantic.EmailStr`, mas pro MVP tá aceitável.
- Sessões expiradas continuam ocupando espaço na tabela porque não tem uma
  limpeza automática — não é grave agora (poucos usuários), mas cresce sem
  controle com o tempo. Precisaria de um job periódico ou apagar no momento
  do login.
- Big O: as operações são todas O(1) (busca por token/email indexado), não é
  o gargalo aqui — o ponto de atenção é mais sobre segurança do token do que
  sobre performance.
