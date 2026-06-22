# Strategic Blueprint

> Focus on the **what** and **why**. The code will follow.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## The Problem
Quero implementar um sistema de autenticacao por email e senha com persistencia em banco. O sistema precisa ter logout funcional, e os dados devem ser armazenados de maneira persistente no SQLite.

## Steps
- [ ] Identificar se já existe alguma estrutura de login, autenticação ou banco de dados.
- [ ] Alterar os arquivos relevantes para implementar um banco de dados SQLite para login (email e senha) de maneira persistente.
- [ ] Criar a página de cadastro, que recebe email e senha do usuário, e salva essas informações no banco.
- [ ] Criar lógica de validação de login, verificando email e senha.
- [ ] Permitir acesso ao sistema apenas após informar email e senha.
- [ ] Garantir que um email tenha apenas uma conta associada

## Success Looks Like
- [ ] Sou capaz de criar uma conta com um email único
- [ ] Só consigo acessar o sistema se informar meu email e minha senha
- [ ] Os dados de login são persistentes entre sessões

## Notes
- [ ] Caso alguém tente criar uma conta com um email que já tem registro, avise com uma pequena mensagem que esse usuário já existe.

---
**⚠️ HUMAN ONLY**: This file is your strategic space. AI agents must not edit it.
