# Strategic Blueprint

> Focus on the **what** and **why**. The code will follow.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## The Problem
O ChatLLM atualmente permite que qualquer pessoa acesse o chat sem se identificar. 
A tarefa é adicionar um fluxo de autenticação para que usuários possam criar uma conta, 
fazer login com email e senha, manter a sessão enquanto usam o sistema e conseguir sair 
da conta com logout.

Os dados de cadastro precisam ficar persistidos em SQLite. O chat só deve estar disponível 
para usuários autenticados.

## Steps
- [ ] Entender a estrutura atual do projeto, principalmente as rotas do backend, o banco SQLite e o fluxo do frontend.
- [ ] Definir como o usuário será representado no banco de dados, com email e senha.
- [ ] Criar o fluxo de cadastro de usuário com validação básica.
- [ ] Criar o fluxo de login com verificação de email e senha.
- [ ] Criar algum mecanismo de sessão/autenticação para identificar o usuário logado.
- [ ] Criar o fluxo de logout para encerrar a sessão do usuário.
- [ ] Proteger o acesso ao chat para impedir uso sem login.
- [ ] Atualizar a interface para permitir cadastro, login e logout.
- [ ] Testar manualmente os principais fluxos e corrigir erros encontrados.

## Success Looks Like
- [ ] Um usuário novo consegue se cadastrar usando email e senha.
- [ ] Os dados do usuário cadastrado ficam salvos no SQLite.
- [ ] Um usuário cadastrado consegue fazer login com credenciais corretas.
- [ ] Um usuário com senha incorreta ou email inexistente não consegue fazer login.
- [ ] Depois do login, o usuário consegue acessar o chat normalmente.
- [ ] Um usuário não autenticado não consegue usar o chat.
- [ ] O usuário consegue fazer logout e voltar para o estado não autenticado.
- [ ] Após logout, o chat deixa de estar acessível até um novo login.
- [ ] Os testes automatizados e/ou testes manuais principais passam.

## Notes
- É preciso decidir uma estratégia simples de autenticação, como sessão por cookie, token ou JWT.
- A senha não deve ser salva em texto puro no banco.
- Tratar casos como email já cadastrado, campos vazios, senha errada e tentativa de acessar o chat sem login.
- Manter a solução simples, porque a tarefa parece focada em autenticação básica e persistência.
- Conferir se já existem padrões de rotas, modelos e banco no projeto antes de criar novos arquivos.

---
**⚠️ HUMAN ONLY**: This file is your strategic space. AI agents must not edit it.
