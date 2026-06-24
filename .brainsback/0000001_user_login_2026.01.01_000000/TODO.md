# Strategic Blueprint

> Focus on the **what** and **why**. The code will follow.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## The Problem
Atualmente o chat não possui uma pagina de login de acesso, quero adicionar um sistema de contas: o usuário se cadastra com email e senha, faz login para usar o chat, e pode fazer logout Os usuários devem ficar salvos no banco SQLite

## Steps
- [ ] Criar uma tabela/modelo de usuário no banco (email, senha)
- [ ] Criar endpoint de cadastro (registrar email e senha)
- [ ] Criar endpoint de login (validar email e senha)
- [ ] Criar endpoint de logout
- [ ] Adicionar tela de login/cadastro no frontend
- [ ] Testar tudo

## Success Looks Like
- [ ] Consigo criar uma conta nova e ela aparece no banco
- [ ] Consigo fazer login com email e senha corretos
- [ ] Login com senha errada é recusado
- [ ] Consigo fazer logout
- [ ] A senha não fica salva como texto puro (usar hash)

## Notes
- [ ] Usar biblioteca para criptografar a senha (bcrypt/passlib)
- [ ] Tratar email já cadastrado e senha incorreta

---
**⚠️ HUMAN ONLY**: This file is your strategic space. AI agents must not edit it.
