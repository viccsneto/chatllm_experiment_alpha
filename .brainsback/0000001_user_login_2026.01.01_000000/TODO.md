# Strategic Blueprint

> Focus on the **what** and **why**. The code will follow.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## The Problem
Nesta primeira tarefa, nosso objetivo é criar um sistema de login e logout de usuários. O cadastro dos usuários deve conter e=mail e senha. A ideia principal é que apenas usuários logados consigam interagir com o chat. Além disso, é importante que as senhas sejam armazenadas no banco de dados de maneira segura.

## Steps
- [X] Criar modelo no banco de dados, cada usuário deve ter nome, email, senha (armazenada com criptografia) e resposta à pergunta de segurança no momento de login (também criptografada)
- [X] Implementar back-end para suportar a criação de contas, incluindo uma pergunta de segurança caso seja necessário trocar a senha.
- [X] Implementar back-end para logica de login, com funções envolvidas
- [X] Implementar back-end para suportar o logout, com funções envolvidas
- [X] Criar elementos de front-end relacionados a login e logout, inclusive mensagens de sucesso e falha
- [X] Conectar elementos de front com elementos de back
- [X] Testar cenários

## Success Looks Like
- [X] Ao acessar o chat, devemos estar na tela de login.
- [X] O usuário consegue criar sua conta com as informações necessárias (nome, email, senha, pergunta de segurança e resposta da pergunta de segurança)
- [X] O usuário consegue fazer logout
- [X] O usuário consegue fazer login
- [X] Um usuário não consegue criar duas contas com o mesmo e-mail, mas deve poder alterar sua senha caso tenha esquecido, mediante resposta à pergunta de segurança.
- [X] Há mensagens compreensivas de erro quando pertinente
- [X] Usuários conseguem trocar sua senha e a senha antiga não funciona mais

## Notes
- [X] Interação com o chat não deve ser possível se o usuário não estiver logado
- [X] Devemos ter mensagens de erro claras com volta direta pra tela de login/criação de usuário
- [X] Devemos ter uma explicação do lado do campo de palavra de segurança no front, explicando que é pra caso a pessoa esqueça a senha, então ela precisa usar uma pergunta que lembre da resposta.

---
**⚠️ HUMAN ONLY**: This file is your strategic space. AI agents must not edit it.
