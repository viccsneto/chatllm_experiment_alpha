# Strategic Blueprint

> Focus on the **what** and **why**. The code will follow.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## The Problem
Preciso implementar login e cadastro por email e senha, guardando tudo no SQLite,
e um logout que realmente funcione (não só sumir o botão, mas invalidar a sessão).

## Steps
- [ ] Ver como criar a tabela de usuário (email, senha) — acho que vou usar uma lib
      pronta (fastapi-users) porque não confio em mim pra fazer hash de senha certo sozinha
- [ ] Configurar o banco SQLite pra guardar os usuários
- [ ] Fazer a rota de cadastro (signup) funcionar
- [ ] Fazer a rota de login funcionar
- [ ] Entender se vou usar cookie ou token pra manter o usuário logado — acho que cookie é
      mais simples de não estragar
- [ ] Fazer o logout invalidar a sessão de verdade
- [ ] Testar se os dados continuam lá depois que eu reinicio o backend

## Success Looks Like
- [ ] Consigo criar uma conta com email/senha e ela fica salva no banco
- [ ] Login funciona com a conta certa e dá erro com senha errada
- [ ] Se eu não tiver logada, não consigo acessar uma rota que devia ser protegida
- [ ] Depois do logout, não consigo mais acessar essa rota protegida
- [ ] Reinicio o backend e minha conta continua existindo (não sumiu)

## Notes
- Tenho medo de guardar a senha errado (tipo, sem hash) — preciso confirmar que
  isso não vai acontecer
- Não sei ainda se o SQLite vai dar algum problema com múltiplos acessos ao
  mesmo tempo, vou testar
- Preciso lembrar de não deixar nenhuma chave/segredo direto no código

---
**⚠️ HUMAN ONLY**: This file is your strategic space. AI agents must not edit it.
