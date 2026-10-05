# Interface web (sem login)

**Data:** 04/10/2026 · **Status:** implementada · **Origem:** `specs/001-interface-web/` (spec, plan e tasks completos)

## O quê
Telas jogáveis do CircuitCrash no navegador do computador e do celular, com dados de exemplo: partida de demonstração no tabuleiro 7×7, perfil do jogador, loja de avatares, ranking, regras e uma página inicial. Um seletor **Demo como** alterna entre um jogador veterano (`voltz_br`) e um novato (`luma_dev`).

## Por quê
A dupla precisa mostrar o jogo funcionando antes de existir login e banco de dados. As telas falam com um repositório trocável, para que o banco entre depois sem refazer nenhuma tela.

## Critérios de aceitação

### Partida de demonstração
1. **Dado** o tabuleiro na rodada 6, **quando** escolho uma peça da mão e toco numa casa vazia ligada ao meu circuito, **então** a peça aparece no tabuleiro, a rodada avança e recebo uma peça nova na mão.
2. **Dado** uma casa vazia que não se liga ao meu circuito, **quando** toco nela, **então** a jogada é recusada com uma mensagem e a rodada não avança.
3. **Dado** qualquer peça no tabuleiro, inclusive de adversário, **quando** toco nela, **então** ela gira 90° no sentido horário.
4. **Dado** que meu circuito liga minha base à fonte, **quando** ele encosta num objetivo, **então** capturo o objetivo e ganho os pontos dele.
5. **Dado** a rodada 12 concluída, **então** vejo a classificação final, com +3 pontos para quem estiver energizado e as Fagulhas de cada colocação.
6. Posso girar a peça da mão antes de colocar, passar a vez e recomeçar a demonstração.

### Perfil
7. Um jogador sem avatar vê a inicial do apelido num quadrado cinza tracejado e uma barra de progresso até o primeiro avatar.
8. Um jogador com menos de 5 partidas vê o rating marcado como provisório.
9. Tocar num avatar do inventário passa a usá-lo.

### Loja
10. Cada avatar mostra a raridade e um destes estados: em uso, já é seu, dá para trocar, faltam Fagulhas, exclusivo.
11. Trocar desconta o preço (Comum 150, Raro 400, Épico 900, Lendário 2000) e coloca o avatar no inventário. Se for o primeiro avatar, ele já passa a ser usado.
12. Avatares exclusivos não podem ser comprados.
13. A loja filtra por raridade.

### Início, ranking e regras
14. O início mostra o botão de partida rápida, as missões do dia e o top 5.
15. O ranking lista só jogadores com 5 partidas ou mais, do maior para o menor rating.
16. A página de regras explica turno, energia, pontuação e Fagulhas.

### Para todas as telas
17. Toda jogada, compra e troca de avatar é validada no servidor.
18. As telas funcionam sem HTMX e sem rolagem horizontal a 390 px e a 1440 px.
19. Nenhuma tela exige login.
20. `pytest`, `ruff` e `mypy` passam.

## Fora do escopo
- Login Google.
- Banco de dados (os dados ficam em memória e voltam ao início quando o servidor reinicia).
- Multiplayer em tempo real.
- Adversários que jogam sozinhos.
- Cartas especiais.
