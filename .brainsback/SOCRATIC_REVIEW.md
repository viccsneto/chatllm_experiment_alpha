# Socratic Review Record

## Question 1 — Task 1: O que foi implementado?

**Reviewer:** O que foi implementado na Tarefa 1?

**Developer:** Usuários podem se cadastrar e fazer login e logout, além do mais foi implementado rastreamento de sessões por aparelhos.

## Question 2 — Task 1: Module Explanation

**Reviewer:** Explique como os componentes `backend/services/auth.py`, `backend/routers/auth.py` e `backend/models.py` interagem entre si sem olhar o código-fonte. Como os dados fluem do endpoint HTTP até o banco de dados e vice-versa?

**Developer:** Em backend/routers/auth.py são definidas todas as rotas http para lidar com cadastro, login, logout e sessão do usuário. em backend/services/auth.py é aplicada toda a regra de negócio relacionadas as rotas anteriores, em backend/models.py são definidas as tabelas no banco de dados relacional que persistem os dados dos usuários, também são lidas pelos services na aplicação das regras de negócio.

## Question 3 — Task 1: Debugging Autonomy

**Reviewer:** Suponha que um usuário tenta fazer login e recebe "Email ou senha incorretos" mesmo digitando a senha correta. O hash armazenado no banco está no formato `key_id:hash`, mas a chave correspondente foi removida da tabela `hashing_keys` (por exemplo, durante uma rotação mal feita). Como você investigaria e resolveria esse problema sem o auxílio de ferramentas de IA?

**Developer:** Investigaria iniciando uma instância local da aplicação python com logs ricos conectada ao banco de produção para validar o ponto de falha. Uma vez encontrado corrigiria a inconsistência na tabela de hashing keys.

## Question 4 — Task 1: Logic Justification

**Reviewer:** A implementação usa HMAC-SHA256 com uma chave do servidor em vez de bcrypt/argon2 para hash de senha, que são os padrões da indústria. Além disso, adotou múltiplas chaves rotacionáveis em tabela separada ao invés de uma única chave fixa no `.env`. Por que essa abordagem foi escolhida, e qual foi a principal preocupação de segurança que motivou o sistema de múltiplas chaves?

**Developer:** Para a chave HMAC para hash, decidi seguir com a recomendação da IA pois eu não podia pesquisar autonomamente fora do editor de código. Quanto à possibilidade de várias chaves, é para questões de segurança: caso uma chave vaze, marco como inativa no banco.

## Question 5 — Task 1: Onboarding Capability

**Reviewer:** Se um novo desenvolvedor entrasse no projeto agora, você conseguiria explicar o fluxo completo de autenticação — desde o momento em que o usuário digita email e senha no frontend até a resposta ser exibida — sem que ele precisasse ler cada linha gerada por IA?

**Developer:** Sim.

## Question 6 — Task 1: Satisfaction

**Reviewer:** Você está satisfeito com o resultado da implementação da Tarefa 1? Há algo que você faria diferente ou melhoraria?

**Developer:** Estou satisfeito. Mas queria fazer melhorias.

## Question 1 — Task 2: O que foi implementado?

**Reviewer:** O que foi implementado na Tarefa 2?

**Developer:** Histórico de chats na barra lateral com título definido após primeira troca de mensagem no chat. Usuário pode criar novas abas de chat. Abas de chat são persistidas no backend.

## Question 2 — Task 2: Module Explanation

**Reviewer:** Explique como o fluxo de criação de uma nova sessão e envio da primeira mensagem funciona da interface do usuário até o banco de dados e volta — quais módulos são envolvidos, qual a ordem das chamadas, e como o título automático é gerado e retornado ao frontend.

**Developer:** Não sei responder.

## Question 3 — Task 2: Debugging Autonomy

**Reviewer:** Suponha que após enviar a primeira mensagem em uma nova sessão, o título nunca aparece na sidebar — ele fica como "Nova sessão...". O backend não está lançando nenhum erro visível. Como você investigaria a causa desse problema sem usar IA?

**Developer:** Entenderia o fluxo do código criado pela IA, para então iniciar a aplicação python localmente e tentar reproduzir o erro em ambiente controlado.

## Question 4 — Task 2: Logic Justification

**Reviewer:** A autenticação nas rotas de chat e sessões foi implementada manualmente em cada endpoint (função `_resolve_user` + verificação de email), em vez de usar um middleware global de autenticação. Por que essa decisão foi tomada, e que vantagens ou desvantagens você vê nessa abordagem?

**Developer:** Deixei a IA fazer nesse formato por ter pouco conhecimento de Python e FastAPI. Middlewares são coisas comuns do meu dia a dia como desenvolvedor, mas a pouca familiaridade com a linguagem e lib me fizeram pular essa etapa.

## Question 5 — Task 2: Onboarding Capability

**Reviewer:** Se um novo desenvolvedor entrasse no projeto agora, você conseguiria explicar o funcionamento completo da barra lateral de sessões — como as sessões são criadas, listadas, selecionadas, como o histórico é carregado e como o título automático funciona — sem que ele precisasse ler cada linha gerada por IA?

**Developer:** Não saberia.

## Question 6 — Task 2: Satisfaction

**Reviewer:** Você está satisfeito com o resultado da implementação da Tarefa 2? Há algo que você faria diferente ou melhoraria?

**Developer:** Pelo que usei no frontend estou satisfeito, mas melhoraria a aparência.

## Comparative Question

**Reviewer:** Como você compara sua experiência entre executar a Tarefa 1 (controlada pelo pipeline) e a Tarefa 2 (implementação livre)?

**Developer:** A tarefa 1 foi mais demorada e "difícil" que a 2, mas tenho muito mais conhecimento sobre o que foi implementado e defini boa parte da arquitetura. Coisa que na 2 deixei tudo para o agente fazer.