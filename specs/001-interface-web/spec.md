# Spec 001 — Interface web (sem login)

**Branch:** `001-interface-web` · **Status:** implementada · **Criada em:** 04/10/2026 · **Dono:** Pessoa A (front-end)

## Contexto
O CircuitCrash precisa de telas jogáveis no navegador do computador e do celular antes de existir login e banco de dados. Esta spec entrega a interface com dados de exemplo, para apresentação e para que o banco possa ser ligado depois sem refazer telas.

Fora do escopo: login Google, banco de dados, multiplayer em tempo real, adversários que jogam sozinhos, cartas especiais.

## Histórias de usuário

### H1 — Jogar uma partida de demonstração (prioridade P1)
Como jogador, quero jogar uma partida no tabuleiro 7×7 para entender o jogo.

**Teste independente:** abrir `/partida`, colocar uma peça ao lado do próprio circuito e ver o placar mudar.

Critérios de aceitação:
1. **Dado** o tabuleiro na rodada 6, **quando** escolho uma peça da mão e toco numa casa vazia ligada ao meu circuito, **então** a peça aparece no tabuleiro, a rodada avança e recebo uma peça nova na mão.
2. **Dado** uma casa vazia que não se liga ao meu circuito, **quando** toco nela, **então** a jogada é recusada com uma mensagem e a rodada não avança.
3. **Dado** qualquer peça no tabuleiro, inclusive de adversário, **quando** toco nela, **então** ela gira 90° no sentido horário.
4. **Dado** que meu circuito liga minha base à fonte, **quando** ele encosta num objetivo, **então** capturo o objetivo e ganho os pontos dele.
5. **Dado** a rodada 12 concluída, **então** vejo a classificação final com as Fagulhas de cada colocação.
6. Posso girar a peça da mão antes de colocar, passar a vez e recomeçar a demonstração.

### H2 — Ver meu perfil (P1)
Como jogador, quero ver avatar, estatísticas, rating, partidas recentes, conquistas, avatares e missões.

Critérios de aceitação:
1. Um jogador sem avatar vê a inicial do apelido num quadrado cinza tracejado e uma barra de progresso até o primeiro avatar.
2. Um jogador com menos de 5 partidas vê o rating marcado como provisório.
3. Tocar num avatar do inventário passa a usá-lo.

### H3 — Trocar Fagulhas por avatares na loja (P1)
Critérios de aceitação:
1. Cada avatar mostra raridade e um destes estados: em uso, já é seu, dá para trocar, faltam Fagulhas, exclusivo.
2. Trocar desconta o preço (Comum 150, Raro 400, Épico 900, Lendário 2000) e coloca o avatar no inventário. Se for o primeiro avatar, ele já passa a ser usado.
3. Avatares exclusivos não podem ser comprados.
4. A loja filtra por raridade.

### H4 — Início, ranking e regras (P2)
1. O início mostra o botão de partida rápida, as missões do dia e o top 5.
2. O ranking lista só jogadores com 5 partidas ou mais, do maior para o menor rating.
3. A página de regras explica turno, energia, pontuação e Fagulhas.

### H5 — Demonstração com dois perfis (P2)
Como apresentador, quero alternar entre um jogador veterano e um novato para mostrar os dois estados.

## Requisitos funcionais
- **RF-01** O tabuleiro tem 7×7 casas: fonte no centro, uma base por jogador nos cantos, objetivos e casas bloqueadas.
- **RF-02** A energia só passa por peças do próprio jogador. Fonte e objetivos são pontas.
- **RF-03** A partida termina depois da rodada 12, com +3 pontos para quem estiver energizado.
- **RF-04** Toda ação é validada no servidor.
- **RF-05** As telas funcionam com e sem HTMX.
- **RF-06** Os dados vêm de um repositório trocável; nesta spec, em memória.
- **RF-07** Nenhuma tela exige login.

## Critérios de sucesso
- **CS-01** Todas as telas abrem sem rolagem horizontal a 390 px e a 1440 px.
- **CS-02** Uma jogada responde em menos de 300 ms no computador local.
- **CS-03** `pytest`, `ruff` e `mypy` passam.
- **CS-04** Alguém que nunca viu o jogo consegue colocar uma peça válida em menos de 1 minuto, guiado só pelas mensagens da tela.

## Entidades
Jogador, Avatar (raridade e preço), Inventário, Resumo de partida, Missão, Conquista, Estado da partida (casas, mão, pontos, rodada).
