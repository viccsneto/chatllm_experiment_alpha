# Strategic Blueprint

> Focus on the **what** and **why**. The code will follow.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## The Problem
Precisamos estabelecer um sistema de identidade e controle de acesso para a aplicação. O objetivo é permitir que usuários se registrem e autentiquem de forma segura usando e-mail e senha, garantindo que o estado da autenticação e as credenciais sejam preservados no banco de dados entre reinicializações do sistema. Isso é fundamental para proteger recursos restritos, verificar a identidade de quem acessa o sistema e manter a persistência confiável dos perfis de usuário.

## Steps
- [ ] **Modelagem de Dados:** Definir o esquema da entidade de Usuário no SQLite, contemplando campos para e-mail (único) e um armazenamento seguro para a senha (hash).
- [ ] **Fluxo de Cadastro (Register):** Criar a lógica de registro que receba as credenciais, valide a integridade dos dados (ex: formato de e-mail), aplique uma função de hash segura na senha e insira o registro no banco.
- [ ] **Fluxo de Login:** Estabelecer a rota de autenticação que consulte o SQLite pelo e-mail, compare a senha fornecida com o hash armazenado e, caso seja compatível, inicie uma sessão segura (via token ou cookie).
- [ ] **Fluxo de Logout:** Implementar o mecanismo que invalide ou destrua a sessão ativa, revogando o acesso do usuário logado.
- [ ] **Proteção de Acesso:** Criar um middleware/validador que intercepte requisições a rotas privadas, exigindo uma sessão de autenticação válida.

## Success Looks Like
- [ ] O registro de um novo usuário salva com sucesso uma nova linha no SQLite, e a coluna de senha contém um hash irreversível, não o texto plano.
- [ ] Tentativas de cadastrar um e-mail já existente no SQLite são bloqueadas e retornam um erro claro de conflito.
- [ ] O login com credenciais corretas estabelece uma sessão válida e permite o acesso a rotas protegidas.
- [ ] O login com senha incorreta ou e-mail inexistente é rejeitado de forma genérica (ex: "Credenciais inválidas"), sem vazar qual dos dois parâmetros estava errado.
- [ ] Após o acionamento do logout, qualquer tentativa subsequente de acessar uma rota protegida com a sessão antiga é negada imediatamente.

## Notes
- [ ] **Estratégia de Segurança:** É estritamente proibido salvar senhas em texto plano. O agente deve escolher e implementar um algoritmo de hash robusto e atual (como `bcrypt` ou `argon2`).
- [ ] **Prevenção de SQL Injection:** Todas as interações com o SQLite devem utilizar *prepared statements* ou parametrização adequada para evitar injeções maliciosas.
- [ ] **Gerenciamento de Sessão:** A decisão entre usar JWT (stateless) ou Cookies de Sessão (stateful) fica a cargo do agente, desde que a implementação garanta o rastreio seguro do usuário autenticado.

---
**⚠️ HUMAN ONLY**: This file is your strategic space. AI agents must not edit it.
