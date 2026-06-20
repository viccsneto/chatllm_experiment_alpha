# Socratic Review Record

> AI-generated. Human must not edit this file.

## Task 1 — Login e Logout

### Question 1 — Opening: What was implemented?

**Reviewer:** O que foi implementado na Tarefa 1?

**Developer:** Foi implementado o cadastro e sistema de login de usuários para o chat.

---

### Question 2 — Module Explanation

**Reviewer:** Explique como os componentes do frontend (Auth.jsx, api.js) se comunicam com as rotas de autenticação no backend (routers/auth.py) para realizar o fluxo de cadastro e login. Qual o papel de cada um?

**Developer:** Eles se comunicam através de API. O arquivo auth.py dita como são as chamadas e o que acontece durante elas, ele que realiza de fato a configuração. O Auth.jsx renderiza os forms e diz qual a ligação de cada um com qual função. Já o api.py diz quais são as chamadas relacionadas a cada função.

---

### Question 3 — Debugging Autonomy

**Reviewer:** Suponha que um usuário tenta redefinir a senha, responde à pergunta de segurança corretamente, mas ao definir a nova senha, recebe "Email nao encontrado." — mesmo tendo usado o mesmo email na etapa anterior. Como você investigaria esse bug sem o auxílio de ferramentas de IA?

**Developer:** Olharia os logs do servidor para entender qual arquivo e chamada gerou a exceção.

---

### Question 4 — Logic Justification

**Reviewer:** A estratégia de autenticação escolhida foi usar JWT (HS256) com bcrypt para senhas, em vez de sessões tradicionais baseadas em cookie/servidor. Por que você acha que essa abordagem foi adotada, e que trade-offs ela traz?

**Developer:** Pelo que conheço e pesquisei, ela faz mais sentido por ser muito mais segura e universal, não pode ser copiada de um canto pra outro por exemplo.

---

### Question 5 — Onboarding Capability

**Reviewer:** Se um novo desenvolvedor entrasse no projeto agora, você conseguiria explicar o fluxo completo de autenticação — desde o momento em que o usuário digita email e senha até o chat ser exibido — sem que ele precisasse ler cada linha do código?

**Developer:** Acho que sim, mas não tenho certeza.

---

### Question 6 — Closing: Satisfaction

**Reviewer:** Você está satisfeita com o resultado da implementação da Tarefa 1? Há algo que você faria diferente?

**Developer:** Estou satisfeita. Faria algumas melhorias se tivesse o tempo necessário, mas a critério do experimento, acho que está satisfatório.

---

## Task 2 — Sessões de Chat com Título Automático

### Question 1 — Opening: What was implemented?

**Reviewer:** O que foi implementado na Tarefa 2?

**Developer:** Criação de histórico de chats como vemos em outros modelos, além de mais detalhes pra os chats, que agora se mantém com histórico e possuem nomes.

---

### Question 2 — Module Explanation

**Reviewer:** Explique como a Sidebar.jsx e o App.jsx se comunicam com o backend para listar, criar e alternar entre sessões. Qual o fluxo de dados quando o usuário clica em uma sessão na barra lateral?

**Developer:** Não consigo explicar em detalhes. Essa segunda tarefa acaba sendo um pouco exaustiva depois da primeira e muito de mim foi confiado no agente.

---

### Question 3 — Debugging Autonomy

**Reviewer:** Durante o desenvolvimento, encontramos um erro `DetachedInstanceError: Instance <User> is not bound to a Session`. Ele ocorria no `event_generator` do `chat_stream`, ao tentar acessar `current_user.id`. Por que esse erro acontece com `StreamingResponse`, e como você explicaria a solução que foi adotada?

**Developer:** Tinha a ver com diferentes objetos estarem sendo criados em tempos diferentes. Foi solucionado ao pegarmos todas as variáveis/parâmetros relevantes nos momentos certos.

---

### Question 4 — Logic Justification

**Reviewer:** A decisão foi criar a sessão somente no momento do primeiro envio de mensagem (via `get_or_create_session`), em vez de criar uma sessão vazia quando o usuário clica em "Novo chat". Qual você acha que foi a lógica por trás dessa escolha, e que impacto ela tem no título automático?

**Developer:** Se não fosse assim, teríamos várias conversas vazias mesmo sem o usuário interagir nos respectivos chats. Não faria sentido e poderia deixar as coisas confusas pro usuário.

---

### Question 5 — Onboarding Capability

**Reviewer:** Se um novo desenvolvedor entrasse no projeto agora, você conseguiria explicar como as sessões funcionam — desde a criação até a exibição do histórico — sem que ele precisasse ler cada linha do código?

**Developer:** Não.

---

### Question 6 — Closing: Satisfaction

**Reviewer:** Você está satisfeita com o resultado da implementação da Tarefa 2? Há algo que você faria diferente?

**Developer:** Acho que foi bem implementado, mas não tive muita participação além de dizer o que tava dando errado. Na tarefa 1 tive participação mais ativa. Então acaba sendo meio frustrante e não sinto que realmente fiz isso.

---

## Comparative Question

**Reviewer:** Como você compara sua experiência entre executar a Tarefa 1 (controlada pelo pipeline, com TODO.md, REACTO.md, participação mais ativa) e a Tarefa 2 (livre, sem artefatos obrigatórios)? O que funcionou melhor para você?

**Developer:** Com certeza a tarefa 1, já que consegui ter mais autonomia enquanto mantinha mais organização.

---