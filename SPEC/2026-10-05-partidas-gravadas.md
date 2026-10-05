# Partidas gravadas, Fagulhas e rating

**Data:** 05/10/2026 · **Status:** implementada, aguardando revisão no PR · **Branch:** `006-partidas-gravadas` · **Detalhes:** `specs/006-partidas-gravadas/`

## O quê
Quando a partida da tela `/partida` termina, o resultado do jogador fica gravado: colocação, pontos, variação de rating e Fagulhas ganhas. Na mesma hora, o perfil do jogador recebe as Fagulhas (respeitando o limite diário), o rating novo e os contadores de partidas, vitórias e objetivos capturados. A tela de fim de partida mostra esse resultado, e a partida aparece no topo das partidas recentes do perfil.

O rating segue o sistema Elo, comparando o jogador com cada um dos três adversários. As Fagulhas seguem a tabela que já está nas regras: 1º +40, 2º +25, 3º +15 e 4º +10 na ranqueada, metade na casual, e no máximo 400 por dia.

## Por quê
Hoje a partida termina e nada muda: a tela promete Fagulhas que nunca chegam, e o perfil e o ranking só mostram dados de exemplo. As specs 001 e 002 deixaram de propósito para depois "gravar as partidas jogadas" e "aplicar Fagulhas e rating ao fim da partida". Com isto, a demonstração mostra o ciclo completo do jogo: jogar, ganhar Fagulhas, trocar por avatar na loja e subir no ranking.

## Critérios de aceitação

### A partida terminada fica gravada
1. **Dado** uma partida em andamento, **quando** ela termina, **então** o resultado do jogador é gravado uma única vez, mesmo que a tela de fim seja aberta ou atualizada de novo.
2. **Dado** uma partida gravada, **quando** abro o perfil, **então** ela aparece primeiro nas partidas recentes, marcada como "hoje", com colocação, pontos, variação de rating e Fagulhas.
3. **Dado** o banco configurado, **quando** o servidor reinicia, **então** a partida gravada e os valores novos do perfil continuam lá.
4. Uma partida que não terminou (o jogador começou outra ou fechou a página) não é gravada.

### Fagulhas
5. **Dado** uma partida ranqueada, **então** o jogador ganha 40, 25, 15 ou 10 Fagulhas pela colocação de 1º a 4º.
6. **Dado** uma partida casual, **então** ganha a metade, arredondada para baixo.
7. **Dado** que o jogador já ganhou Fagulhas hoje, **então** a soma do dia nunca passa de 400: ele recebe só o que falta para o limite, e a tela de fim avisa quando o limite cortou o ganho.
8. Fagulhas gastas na loja não devolvem espaço no limite do dia.

### Rating
9. **Dado** o fim de uma partida ranqueada, **então** o rating muda pelo Elo: para cada adversário, conta vitória se o jogador ficou à frente, derrota se ficou atrás e empate se fez os mesmos pontos.
10. Ganhar de adversários com rating maior rende mais do que ganhar de adversários com rating menor, e o 1º lugar nunca perde rating.
11. Enquanto o jogador está no período provisório (menos de 5 partidas), o rating muda mais rápido, para encontrar o nível dele logo.
12. Partida casual não muda o rating.
13. Depois da 5ª partida, o jogador passa a aparecer no ranking.

### Perfil e ranking
14. A partida soma 1 em partidas; o 1º lugar soma 1 em vitórias; os objetivos que o jogador tem capturados no fim somam em objetivos capturados.
15. A tela de fim de partida mostra as Fagulhas ganhas e o rating antes e depois.
16. As Fagulhas ganhas aparecem na hora no cabeçalho e na loja.

### Funciona com ou sem banco
17. Tudo acima vale com os dados em memória e com o banco, e os testes rodam contra os dois.
18. Gravar a partida e atualizar o perfil acontecem juntos: ou os dois ficam gravados, ou nenhum.
19. `pytest`, `ruff` e `mypy` passam.

## Fora do escopo
- Gravar o resultado dos adversários (hoje eles não são contas de jogadores).
- Escolher entre partida ranqueada e casual na tela: a partida de `/partida` é ranqueada. A regra da casual fica pronta e testada para quando houver a escolha.
- Partidas online entre pessoas, temporadas e reinício do ranking.
- Missões e conquistas avançando com as partidas.
- Página com o histórico completo de partidas (o perfil continua mostrando as 5 mais recentes).
- Compra atômica na loja.
