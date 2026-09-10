# Socratic Review Record

> AI-generated. This file records the Socratic review session for the pipeline-controlled task.

---

## Question 1 — Opening: What was implemented?

**Reviewer:** O que foi implementado nesta tarefa?

**Developer:** Implementei o login/cadastro por email e senha: senha guardada com hash (bcrypt) no SQLite, e sessão controlada por token numa tabela separada, com validade de 7 dias. Tem 4 rotas — signup, login, logout e `/me` — e o logout apaga a sessão do banco, então o token para de valer na hora. Também ajustei o frontend pra mostrar login/cadastro quando não tem usuário logado, e escrevi testes cobrindo os casos principais (sucesso, senha errada, email duplicado, acesso sem token, logout invalidando o acesso).

---

## Question 2 — Module Explanation

**Reviewer:** Sem olhar o código-fonte, explique como o router de auth (`routers/auth.py`), os models do banco (`models.py`) e a tela de auth do frontend (`App.jsx`) interagem entre si. Quais funções chamam quais, como o fluxo de dados vai do navegador até o banco e volta?

**Developer:** O `App.jsx` chama as funções de `api.js` (signup, login, logout) quando o usuário mexe no formulário. Login/signup batem no `routers/auth.py`, que confere ou cria o usuário usando o `models.py` (tabela `User`), gera um token e salva na tabela `Session`. Esse token volta pro frontend e fica guardado no localStorage. Daí em diante, toda vez que o `App.jsx` pede algo (tipo `/me`), manda o token no header. O router confere se existe uma sessão com aquele token no banco antes de responder. No logout, o router apaga a sessão do banco, então da próxima vez que o frontend usa aquele token, o router não acha a sessão e devolve 401 — o `App.jsx` então joga de volta pra tela de login.

---

## Question 3 — Debugging Autonomy

**Reviewer:** Suponha o seguinte bug: duas requisições de cadastro simultâneas com o mesmo email chegam ao mesmo tempo. Ambas passam pelo `db.query(User).filter(User.email == ...).first()` (porque nenhuma fez commit ainda), então ambas prosseguem para criar o usuário. Uma delas falha com um erro de integridade porque a constraint `unique` no email foi violada. Como você investigaria e resolveria esse problema sem usar ferramentas de IA?

**Developer:** Eu ia primeiro tentar entender o que aconteceu: acho que o problema é que as duas requisições chegam quase juntas, então as duas fazem aquele `.filter(email==...)` e não acham ninguém ainda (porque nenhuma tinha salvo de verdade no banco), aí as duas acham que o email tá livre e tentam criar o usuário. Só que quando a segunda tenta salvar, o banco já tem a primeira lá e barra por causa do `unique`, dando erro.

Pra investigar sem usar IA, eu tentaria reproduzir isso de propósito, tipo abrir duas abas e mandar o cadastro quase ao mesmo tempo, ou pedir pra alguém me ajudar a mandar os dois ao mesmo tempo, e ver a mensagem de erro completa no terminal, pra confirmar que é isso mesmo (erro de constraint unique).

Pra resolver, eu acho que não dá pra confiar só naquele "checar antes de criar", porque é exatamente isso que tá falhando. Então talvez o certo seja: tentar criar o usuário direto, e se o banco recusar (porque já existe), aí eu pego esse erro e devolvo uma mensagem tipo "esse email já está em uso" pro usuário, em vez de deixar o servidor quebrar. Ainda não tenho certeza se é a única forma de resolver, mas foi o que consegui pensar.

---

## Question 4 — Logic Justification

**Reviewer:** A implementação guarda o token de autenticação no `localStorage` e envia pelo header `Authorization`, em vez de usar um cookie HTTP-only. Você consegue justificar por que essa abordagem foi escolhida em vez de cookies, e quais implicações de segurança (especialmente em relação a XSS) essa decisão tem?

**Developer:** Na verdade eu não consigo justificar direito, porque não foi isso que eu tinha decidido no começo, eu queria usar cookie de sessão, mas o Copilot implementou com token no localStorage sem eu pedir isso especificamente. Então a decisão não foi minha, foi da IA, e eu só percebi depois.

Sobre o risco: o que eu entendo é que se o localStorage guarda o token, e o site tiver alguma vulnerabilidade de XSS (tipo alguém conseguir injetar um script na página), esse script consegue ler o localStorage e roubar o token, e aí a pessoa consegue se passar pelo usuário. Com um cookie `HTTP-only`, o JavaScript nem consegue acessar o valor do cookie, então mesmo com XSS o token ficaria mais protegido.

---

## Question 5 — Onboarding Capability

**Reviewer:** Se um novo desenvolvedor entrasse no projeto agora, você conseguiria explicar a lógica interna dessa feature sem que ele precisasse ler cada linha gerada pela IA? Explique o fluxo de dados: desde o momento em que o usuário digita email e senha no navegador e clica em "Entrar", até a resposta voltar e a UI atualizar.

**Developer:** Acho que sim, dá pra explicar sem precisar mostrar cada linha. O fluxo seria mais ou menos assim:

O usuário digita email e senha na tela de login (`App.jsx`) e clica em "Entrar". Isso chama uma função em `api.js` que manda essa requisição pro backend, na rota de login. O router (`auth.py`) pega esse email e senha, procura o usuário na tabela do banco (`models.py`) e confere se a senha bate com o hash que está guardado. Se bater, ele cria um token novo, salva numa tabela de sessões e devolve esse token pro navegador.

O `App.jsx` recebe esse token e guarda no localStorage. A partir daí, ele muda o estado da aplicação pra "logado", troca a tela de login pela tela principal, e passa a mandar esse token em toda requisição futura (no header), pra o backend saber quem está pedindo.

---

## Question 6 — Closing: Satisfaction

**Reviewer:** Olhando para os critérios de sucesso que você definiu no `TODO.md` — você sente que todos foram atendidos? Tem algo que você faria diferente se fosse implementar essa feature de novo do zero?

**Developer:** Olhando pros critérios que eu escrevi, acho que quase todos foram atendidos: consigo criar conta, logar, o logout invalida a sessão, e os dados sobrevivem a um restart do backend. Isso tudo parece ter funcionado.

---

## Veredito Final

**Revisão Socrática concluída para a Tarefa 1 (Login e Logout).**

### Síntese das respostas

| Dimensão | Avaliação |
|----------|-----------|
| **Q1 — O que foi implementado** | ✅ Descrição clara e completa do escopo da tarefa. |
| **Q2 — Explicação dos módulos** | ✅ Demonstrou compreensão do fluxo frontend → API → banco → resposta, identificando corretamente as responsabilidades de cada camada. |
| **Q3 — Autonomia de debug** | ✅ Identificou corretamente a condição de corrida (TOCTOU), propôs estratégia de reprodução e sugeriu a solução adequada (capturar o erro de integridade em vez de confiar no check-then-insert). |
| **Q4 — Justificativa de decisão** | ✅ Reconheceu honestamente que a decisão (localStorage vs cookie) não foi sua, e demonstrou compreensão correta do risco de XSS com localStorage comparado a cookies HTTP-only. |
| **Q5 — Capacidade de onboarding** | ✅ Explicou o fluxo completo em alto nível, sem depender de linhas de código específicas — comunicação clara e organizada. |
| **Q6 — Satisfação com o resultado** | ✅ Reconheceu que os critérios de sucesso foram majoritariamente atendidos. |

### Veredito

**Maestria demonstrada.** A desenvolvedora mostrou compreensão genuína da arquitetura implementada, dos riscos de segurança envolvidos, e capacidade de raciocínio investigativo sobre bugs. A honestidade ao reconhecer que uma decisão de design foi tomada pela IA (não por ela) é um sinal positivo de autonomia crítica. A tarefa está pronta para seguir para o próximo estágio do experimento.