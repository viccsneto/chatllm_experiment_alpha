# Socratic Review

**Modelo da IA:** GitHub Copilot
**Data:** 2026-06-23

## Verificação de Tarefas
- Tarefa 1 (Login e Logout): Concluída. Sistema de autenticação com cadastro, login e logout via API REST, senhas hasheadas com bcrypt, sessões por token, e interface de usuário no frontend.

## Revisão Reflexiva
O desenvolvedor demonstrou compreensão sólida dos conceitos de segurança e arquitetura da autenticação implementada, articulando corretamente os trade-offs das decisões técnicas.

## Debate Socrático

**Pergunta 1:** Por que a senha do usuário é armazenada como hash bcrypt no banco em vez de texto puro? O que aconteceria se um invasor obtivesse acesso ao arquivo chat.db?
**Resposta:** Porque isso impede um invasor de obter a senha pura. Um texto hasheado ajuda na segurança e evita o fácil acesso dos dados do usuário.
**Avaliação técnica:** Correto. O hash bcrypt com salt aleatório torna ataques de rainbow table inviáveis e impede a exposição da senha original mesmo com acesso ao banco de dados.

**Pergunta 2:** No endpoint POST /api/auth/login, toda vez que o usuário faz login, um novo token é gerado e uma nova sessão é criada. Por que não reutilizamos a sessão existente? Qual o trade-off dessa abordagem?
**Resposta:** Gerar um novo token a cada login facilita o código, evitando a busca do token anterior no banco, e permite multiconectividade entre dispositivos. O custo é o acúmulo de sessões na tabela, que sem expiração só são limpas no logout.
**Avaliação técnica:** Correto. O desenvolvedor identificou corretamente o benefício (suporte a múltiplos dispositivos simultâneos) e o trade-off (acúmulo de sessões órfãs sem política de expiração).

**Pergunta 3:** No frontend, o token de autenticação é salvo no localStorage. Quais as implicações de segurança disso? Se você pudesse escolher uma alternativa, qual seria?
**Resposta:** O localStorage gravado no disco sobrevive a fechar o navegador, mantendo o login. Mas o token continua lá em computador compartilhado, e se o usuário esquecer de fazer logout, qualquer pessoa que abrir o navegador depois entra na conta. Além disso, abre brecha para vulnerabilidade XSS.
**Avaliação técnica:** Correto. O desenvolvedor identificou o risco de persistência em disco, o cenário de computador compartilhado e a vulnerabilidade a XSS. Cookies HttpOnly seriam uma alternativa mais segura.

**Pergunta 4:** Olhando o endpoint de logout: ele recebe o token no corpo da requisição e deleta a sessão do banco. Se o token for roubado antes do logout, o atacante consegue usar a API. Que mecanismo adicional poderia mitigar isso?
**Resposta:** A mitigação mais direta é dar expiração ao token (sozinho ou via esquema access+refresh), de forma que um token roubado deixe de valer após um tempo.
**Avaliação técnica:** Correto. TTL (time-to-live) com expiração é a mitigação padrão. O desenvolvedor também mencionou o padrão access+refresh token, que é a evolução natural para sistemas mais robustos.

## Veredito
**Status:** MASTERY PROVEN

O desenvolvedor demonstrou compreensão adequada dos conceitos de segurança (hashing, XSS, expiração de tokens), arquitetura (trade-offs de design de sessões) e boas práticas de frontend (armazenamento de credenciais). As respostas foram precisas e refletem apropriação técnica do código implementado.