# Strategic Blueprint

> Focus on the **what** and **why**. The code will follow.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## The Problem
Preciso da implementação de uma tela de login. Ela deve ser a primeira tela que o usuário acessa caso não esteja logado. O chat só deve poder ser acessível caso o usuário esteja logado. Para isso, preciso da implementação do Modelo User. A tela deve ser implementada seguindo instruções modernas de UI.

## Steps
- [ ] Crie um Modelo de User, que será um tabela SQLAlchemy. Deve ter todos os dados necessários de um usuário de um MVP simples. id, email (UNIQUE), password_hash, created_at. Caso exsita a necessidade de mais algum aplique.
- [ ] Faça a criação das rotas de autenticação POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me. Códigos HTTP mais adequados podem ser retornados, exemplo 201 para register com sucesso, 409 para register com email duplicado, 401 para auetnticacao com login inválido
- [ ] As rotas POST/api/chat e POST/api/stream precisam ser protegidas pelo middleware
- [ ] Middleware para get_current_user
- [ ] O usuário pode acessar direto o chat armazenando token no localStorage
- [ ] Devem ser realizados Testes com registro, login, logout, acesso negado sem token, email duplicado, etc.

## Success Looks Like
- [ ] O usuário é direcionado para tela inicial caso não esteja logado. Na tela de login deve ter uma interface moderna, com boas práticas de UX/UI. Devem ter campos pro usuário preencher dados de login. Deve poder clicar no botão e realizar login. Deve poder Clicar no botão para criar uma conta. Deve poder fazer login ao preencher uma conta válida. Deve ser negado ao prencher uma conta inválida.
- [ ] A consistencia da criação do usuário, interação das rotas, interface do usuário devem ser testadas durante implementação para garantir bom resultado final.
- [ ] Podem ser usadas telas de login padrão considerads referências para a aplicação de um bom design.

## Notes
- [ ] Token pode ser armazenado em cookie.
- [ ] A senha deve ser um hash. Pode ser utilizada lib para a solução.
- [ ] Pode ser usado Schemas Pydantic (RegisterRequest, LoginRequest, AuthResponse) 
- [ ] Autenticação pode usar JWT. Pode ser usada a lib PyJWT

---
**⚠️ HUMAN ONLY**: This file is your strategic space. AI agents must not edit it.
