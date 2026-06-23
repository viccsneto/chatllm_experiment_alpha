# Strategic Blueprint

> Focus on the **what** and **why**. The code will follow.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## The Problem
_State clearly what you are trying to achieve and the architectural constraints, avoiding implementation specifics of HOW to do it. Focus on WHAT and WHY._

## Steps
- [ ] 1. elaborar um schema para salvar email e senha ou referencia dela (abordaremos isso nos proximos passos) no banco de dados SQLite.
- [ ] 2. elaborar outro schema auxiliar com email do usuário (foreing key) e identificador único e deterministico do aparelho onde o usuário está acessando a plataforma.
- [ ] 3. o backend deve usar algum algortimo assimetrico, leve na medida do possivel, que faça uso de um segredo que só o backend tem acesso e que possa ser rotacionado quando necessário (adicione o segredo para desenvolvimento no .env do repositório).
- [ ] com o algoritmo escolhido no passo anterior deve ser derivado a partir da senha original do usuário um hash que será armazenado no banco de dados.
- [ ] 4. quando o cadastro for realizado com sucesso deve ser retornado um payload com o email do usuário que se cadastrou.
- [ ] 5. para login deve ser usado algoritmo de comparação de tempo constante para comparar o hash gerado com o segredo do backend a partir do input do usuário com o hash armazenado no banco. antes deve ser verificado se o comprimento de ambas as strings são iguais, se forem comprimentos diferentes deve ainda sim ser feita a comparação com tempo constante negada (pseudocode: !timeSafeEqual(userInputHash, dbHash)) para evitar que o cliente descubra a quantidade de bits da senha que deseja descobrir caso esteja tentando invadir o sistema com a diferença dos tempos de resposta.
- [ ] 6. quando o usuário fizer a verificação da senha com sucesso deve ser salvo que está logado em dispositivo X na tabela do passo 2
- [ ] 7. no frontend a sessão do usuário deve ser armazenada no local storage sem expor a senha.
- [ ] 8. ao fazer logout a sessão deve ser removida do local storage após o backend retornar sucesso ao marcar na tabela do passo 2 que o usuário está deslogado no aparelho x.

## Success Looks Like
- [ ] o código executa sem problemas
- [ ] um usuário sem cadastro realizar cadastro sem problemas e um hash de sua senha é armazenado no banco de dados
- [ ] usuário com cadastro consegue fazer login em multiplos dispositivos apenas se passar na validação da senha
- [ ] usuário consegue fazer logout sem problemas
- [ ] após logout só deve conseguir fazer login passando pela validação rigorosa do backend, alterar o local storage do browser não deve permitir login deliberadamente.

## Notes
- [ ] use sempre os verbos e cédigos http mais semânticos para cada situação.
- [ ] se algo não estiver claro muito ambíguo interrogue-me incessantemente até alcançarmos o mesmo entendimento sobre o trabalho que deve ser feito.

---
**⚠️ HUMAN ONLY**: This file is your strategic space. AI agents must not edit it.
