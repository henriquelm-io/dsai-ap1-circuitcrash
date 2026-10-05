# Spec 006 — Partidas gravadas, Fagulhas e rating

**Branch:** `006-partidas-gravadas` · **Status:** proposta, sem código ainda · **Criada em:** 05/10/2026 · **Dono:** Severino (banco de dados) · **Origem:** [SPEC/2026-10-05-partidas-gravadas.md](../../SPEC/2026-10-05-partidas-gravadas.md)

## Contexto
A partida da tela `/partida` termina depois de 12 rodadas e mostra a classificação com "+40 Fagulhas", mas nada é gravado: o jogador não recebe as Fagulhas, o rating não muda e o perfil continua com as partidas de exemplo. A spec 002 deixou isso de fora de propósito ("gravar as partidas jogadas na tela `/partida`" e "aplicar Fagulhas e rating ao fim da partida"), e o próprio plano dela apontou esta spec como a próxima.

Esta spec fecha o ciclo da demonstração: jogar, ganhar Fagulhas, trocar por um avatar na loja e subir no ranking.

Fora do escopo: gravar o resultado dos adversários (não são contas de jogadores), escolher entre ranqueada e casual na tela, partidas online entre pessoas, temporadas, missões e conquistas avançando com as partidas, página de histórico completo e compra atômica na loja.

## Histórias de usuário

### H1 — Minha partida fica gravada (prioridade P1)
Como jogador, quero que a partida que terminei apareça no meu perfil e continue lá depois que o servidor reinicia.

**Teste independente:** jogar até o fim em `/partida`, abrir o perfil e ver a partida no topo das recentes; reiniciar o servidor com o banco e ver de novo.

Critérios de aceitação:
1. **Dado** uma partida em andamento, **quando** ela termina, **então** o resultado é gravado uma única vez, mesmo que a tela de fim seja aberta ou atualizada de novo.
2. **Dado** uma partida gravada, **quando** abro o perfil, **então** ela aparece primeiro nas partidas recentes, como "hoje", com colocação, pontos, variação de rating e Fagulhas.
3. **Dado** o banco configurado, **quando** o servidor reinicia, **então** a partida e os valores novos do perfil continuam lá.
4. **Dado** uma partida que não terminou, **então** nada é gravado.

### H2 — Ganho Fagulhas pela colocação (P1)
Como jogador, quero receber as Fagulhas que a tela de fim promete, para trocar por avatares na loja.

**Teste independente:** terminar uma partida em 1º com 0 Fagulhas ganhas no dia e ver +40 no cabeçalho.

Critérios de aceitação:
1. **Dado** uma partida ranqueada, **então** ganho 40, 25, 15 ou 10 Fagulhas pela colocação de 1º a 4º.
2. **Dado** uma partida casual, **então** ganho a metade, arredondada para baixo.
3. **Dado** que já ganhei Fagulhas hoje, **então** a soma do dia nunca passa de 400: recebo só o que falta, e a tela de fim avisa quando o limite cortou o ganho.
4. Fagulhas gastas na loja não devolvem espaço no limite do dia.
5. As Fagulhas aparecem na hora no cabeçalho e na loja.

### H3 — Meu rating reflete como jogo (P1)
Como jogador, quero que o rating suba quando fico à frente de adversários fortes e caia quando fico atrás de adversários fracos.

**Teste independente:** terminar em 1º e em 4º contra adversários de mesmo rating e ver o rating subir e cair.

Critérios de aceitação:
1. **Dado** o fim de uma partida ranqueada, **então** o rating muda pelo Elo, comparando com cada adversário: vitória se fiquei à frente, derrota se fiquei atrás, empate se fizemos os mesmos pontos.
2. Ficar à frente de adversários com rating maior rende mais do que ficar à frente de adversários com rating menor.
3. O 1º lugar nunca perde rating e o último nunca ganha.
4. No período provisório (menos de 5 partidas), o rating muda mais rápido.
5. Partida casual não muda o rating.
6. Depois da 5ª partida, apareço no ranking.

### H4 — Perfil e fim de partida com dados reais (P2)
Como jogador, quero ver na tela de fim e no perfil o que a partida mudou.

Critérios de aceitação:
1. A partida soma 1 em partidas; o 1º lugar soma 1 em vitórias; os objetivos que tenho capturados no fim somam em objetivos capturados.
2. A tela de fim mostra as Fagulhas ganhas e o rating antes e depois.

## Requisitos funcionais
- **RF-01** Ao fim da partida de `/partida`, o resultado do jogador ativo é gravado uma única vez por partida.
- **RF-02** Fagulhas por colocação na ranqueada: 1º 40, 2º 25, 3º 15, 4º 10. Casual: metade, para baixo.
- **RF-03** Limite de 400 Fagulhas ganhas em partidas por dia, por jogador. O ganho é cortado no que falta para o limite, nunca fica negativo.
- **RF-04** Rating Elo de vários adversários: para cada adversário, esperado = 1 / (1 + 10^((rating dele − meu rating) / 400)); resultado = 1, 0,5 ou 0; variação = arredondar(K / número de adversários × soma de (resultado − esperado)). K = 48 no período provisório e 32 depois.
- **RF-05** Partida casual não muda o rating.
- **RF-06** O mesmo resultado aplica, juntos: Fagulhas, rating, +1 partida, +1 vitória se 1º, + objetivos capturados no fim.
- **RF-07** A gravação da partida e a atualização do jogador acontecem juntas: ou tudo é gravado, ou nada.
- **RF-08** As regras de Fagulhas e rating não dependem de banco, rede nem relógio: o mesmo resultado com os mesmos dados dá sempre os mesmos números.
- **RF-09** Funciona igual com os dados em memória e com o banco.

## Critérios de sucesso
- **CS-01** Terminar uma partida em `/partida` muda as Fagulhas do cabeçalho, o rating e as partidas recentes do perfil, sem erro, no computador e no celular.
- **CS-02** Com o banco, os valores continuam iguais depois de reiniciar o servidor.
- **CS-03** Os testes das regras de Fagulhas e rating cobrem as quatro colocações, a casual, o limite diário, o período provisório e os empates.
- **CS-04** Os testes de gravação rodam contra a memória e contra o banco.
- **CS-05** `pytest`, `ruff` e `mypy` passam.

## Entidades
- **Resultado da partida:** tipo (ranqueada ou casual), colocação, pontos, objetivos capturados, rating antes, variação de rating, Fagulhas ganhas e se o limite do dia cortou o ganho.
- Usa as entidades da spec 002: Jogador, Partida e Participação na partida.

## Pontos para a revisão (precisam do aceite do Henrique)
1. **Mudança no contrato `Repositorio`.** A constituição pede o aceite dos dois. Esta spec acrescenta dois métodos: um que diz quantas Fagulhas o jogador já ganhou em partidas hoje, e um que grava o resultado e atualiza o jogador de uma vez. Nenhum método existente muda.
2. **Rating dos adversários.** Os adversários da demonstração (Lia, Bruno e Kai) não são contas de jogadores e não têm rating. Proposta: valem 1200, o rating inicial. Quando os adversários automáticos (spec do Henrique) entrarem, cada nível pode ter o próprio rating sem mudar estas regras, porque elas recebem os ratings dos adversários de fora.
3. **Quem é "Você" na partida.** É o jogador escolhido em **Demo como** no momento em que a partida termina.
4. **Objetivos capturados.** O tabuleiro não conta capturas ao longo da partida; conta-se quantos objetivos estão capturados pelo jogador no fim.
5. **Conflito com a spec dos adversários automáticos.** As duas mexem na rota e na tela da partida. Esta spec só acrescenta a gravação no fim da partida e o quadro "Seu resultado" na tela de fim, sem mudar as regras do tabuleiro, para o merge ser simples.
