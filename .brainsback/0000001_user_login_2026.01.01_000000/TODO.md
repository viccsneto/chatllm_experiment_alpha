# Strategic Blueprint

> Focus on the **what** and **why**. The code will follow.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## The Problem
O sistema precisa de uma funcionalidade de autenticação segura para gerenciar sessões de usuários. É necessário implementar rotas de cadastro (signup), login e logout. Os dados dos usuários, incluindo senhas, devem ser armazenados em um banco de dados SQLite de forma segura (usando hash). A manutenção das sessões será feita através de JSON Web Tokens (JWT) para proteger rotas restritas, e o processo de logout deve invalidar ativamente a sessão no cliente.

## Steps
- [x] Configurar a conexão com o banco de dados SQLite.
- [x] Criar a tabela/modelo `User` no banco de dados com os campos necessários (ex: `id`, `email`, `password_hash`).
- [x] Implementar a rota de Cadastro (`/signup`):
  - [x] Receber e validar email e senha.
  - [x] Gerar o hash da senha (ex: usando bcrypt).
  - [x] Salvar o novo usuário no SQLite.
- [x] Implementar a rota de Login (`/login`):
  - [x] Validar as credenciais fornecidas contra o banco de dados.
  - [x] Gerar e retornar um token JWT com uma expiração definida.
- [x] Implementar middleware de autenticação para proteger rotas privadas validando o JWT.
- [x] Implementar a rota ou mecanismo de Logout:
  - [x] Remover ou invalidar o JWT no lado do cliente (limpar cookies ou storage).

## Success Looks Like
- [ ] É possível criar um novo usuário e os dados são persistidos no SQLite com a senha hasheada (não em texto plano).
- [ ] O login com credenciais válidas retorna um token JWT válido.
- [ ] O login com credenciais inválidas é rejeitado com o erro apropriado.
- [ ] Rotas protegidas não podem ser acessadas sem um token JWT válido.
- [ ] O logout remove o token com sucesso, impedindo o acesso subsequente a rotas protegidas.

## Notes
- **Senhas:** Nenhuma senha será armazenada em texto plano. Utilizaremos hash `bcrypt` com salt gerado aleatoriamente.
- **Tokens:** Os tokens JWT terão uma expiração curta (ex: 1 hora) e serão assinados com um segredo (secret) mantido seguro através de variáveis de ambiente (`.env`).

---
**⚠️ HUMAN ONLY**: This file is your strategic space. AI agents must not edit it.
