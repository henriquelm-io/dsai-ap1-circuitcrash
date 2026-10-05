# Spec 002 — Banco de dados

**Branch:** `002-banco-de-dados` · **Status:** implementada, aguardando revisão no PR · **Criada em:** 04/10/2026 · **Dono:** parceiro (banco de dados)

## Contexto
A spec 001 entregou as telas com dados de exemplo guardados em memória: toda compra, troca de avatar ou mudança some quando o servidor reinicia. Esta spec guarda os dados da plataforma em um banco de dados de verdade, sem mudar nenhuma tela nem nenhuma regra, para que a demonstração de terça (06/10) mostre que o progresso do jogador fica salvo.

A prioridade é algo simples e funcionando: um banco em arquivo, que não exige instalar nada, e a opção de usar um servidor de banco quando houver um.

Fora do escopo: login Google (só deixamos o espaço para o identificador da conta), gravar partidas jogadas na tela `/partida`, aplicar Fagulhas e rating ao fim da partida, campeonatos, painel de administração e hospedagem.

## Histórias de usuário

### H1 — O progresso do jogador não se perde (prioridade P1)
Como jogador, quero que minhas Fagulhas, meus avatares e o avatar em uso continuem iguais depois que o servidor reinicia.

**Teste independente:** trocar Fagulhas por um avatar na loja, reiniciar o servidor e abrir o perfil.

Critérios de aceitação:
1. **Dado** o banco configurado, **quando** troco Fagulhas por um avatar e o servidor reinicia, **então** o avatar continua no inventário e as Fagulhas continuam descontadas.
2. **Dado** o banco configurado, **quando** passo a usar outro avatar e o servidor reinicia, **então** o perfil e o cabeçalho mostram o avatar escolhido.
3. **Dado** qualquer operação, **então** as Fagulhas de um jogador nunca ficam negativas.

### H2 — A demonstração continua igual (P1)
Como apresentador, quero que o banco comece com os mesmos jogadores, avatares, inventários, partidas, missões e conquistas da spec 001.

Critérios de aceitação:
1. **Dado** um banco vazio, **quando** rodo a carga de exemplo, **então** todas as telas mostram o mesmo conteúdo que mostravam com os dados em memória.
2. **Dado** um banco que já tem dados, **quando** rodo a carga de novo, **então** nada é duplicado.
3. Consigo apagar tudo e recarregar os dados de exemplo com um único comando, para recomeçar a apresentação.

### H3 — Funciona com ou sem banco (P1)
Como desenvolvedor, quero escolher entre os dados em memória e o banco por uma configuração, sem mudar código.

Critérios de aceitação:
1. **Dado** que a configuração do banco está vazia, **então** o sistema funciona como na spec 001, com dados em memória.
2. **Dado** um endereço de banco em arquivo, **então** o sistema usa esse arquivo.
3. **Dado** um endereço de servidor de banco, **então** o sistema usa esse servidor.
4. As regras da loja e do ranking se comportam igual nos dois modos.

### H4 — Pronto para o login Google (P2)
Como dupla, queremos que o cadastro de jogadores já tenha onde guardar o identificador da conta Google, para que a spec de login não precise refazer a estrutura dos dados.

Critérios de aceitação:
1. Cada jogador pode ter um identificador de conta Google, único entre os jogadores e vazio por enquanto.
2. Nenhuma senha é guardada.

## Requisitos funcionais
- **RF-01** Os dados de jogadores, avatares, inventários, partidas recentes, missões e conquistas ficam guardados no banco.
- **RF-02** O contrato `Repositorio` da spec 001 não muda: as telas e as regras usam os mesmos métodos.
- **RF-03** Fagulhas nunca ficam negativas, mesmo que alguém tente gravar um valor errado direto no banco.
- **RF-04** Apelido, e-mail e identificador Google são únicos entre os jogadores.
- **RF-05** O ranking mostra só jogadores com 5 partidas ou mais, do maior para o menor rating.
- **RF-06** A ordem de jogadores e avatares é a mesma da spec 001 (os dois primeiros jogadores são os perfis da demonstração; a loja lista do Comum ao Exclusivo).
- **RF-07** A estrutura do banco é criada e atualizada por migrações versionadas, nunca à mão.
- **RF-08** Sem configuração de banco, o sistema usa os dados em memória.
- **RF-09** O endereço e a senha do banco ficam só no `.env`.

## Critérios de sucesso
- **CS-01** Os testes da loja e do ranking passam contra os dados em memória e contra o banco.
- **CS-02** Com o banco em arquivo, todas as telas abrem sem erro e com o mesmo conteúdo da spec 001.
- **CS-03** Uma compra feita antes de reiniciar o servidor aparece depois de reiniciar.
- **CS-04** Alguém da dupla consegue criar o banco e carregar os dados de exemplo seguindo só o README, em menos de 5 minutos.
- **CS-05** `pytest`, `ruff` e `mypy` passam.

## Entidades
Jogador (com identificador Google opcional), Avatar, Item de inventário, Partida, Participação na partida, Missão, Progresso de missão no dia, Conquista, Progresso de conquista.

## Pontos em aberto para a revisão
1. **Compra em uma transação.** O `docs/banco-de-dados.md` pede que a compra (descontar Fagulhas e adicionar ao inventário) aconteça numa só transação. Com o contrato atual, a loja faz duas chamadas separadas. Proposta para terça: manter o contrato como está e confiar nas validações da loja mais a trava de Fagulhas não negativas no banco. Uma operação de compra atômica no contrato fica para uma próxima spec, com o aceite dos dois.
2. **Teste da loja que altera o objeto em memória.** O teste `test_compra_desconta_e_equipa_primeiro_avatar` muda as Fagulhas do jogador sem chamar `salvar_jogador` e confere o resultado no mesmo objeto. Isso só funciona em memória. Proposta: o teste passa a salvar o jogador e a reler do repositório, o que vale para as duas implementações.
3. **Missões do dia.** Em memória, as missões são fixas. No banco, o progresso é por dia: o progresso de exemplo é carregado para o dia da carga e volta a zero no dia seguinte, até a spec de missões existir.
