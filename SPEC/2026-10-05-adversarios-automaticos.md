# Adversários automáticos

**Data:** 05/10/2026 · **Status:** em implementação · **Branch:** `010-adversarios-automaticos` · **Detalhes:** `specs/010-adversarios-automaticos/`

## O quê
Na partida da tela `/partida`, Lia, Bruno e Kai passam a jogar sozinhos. Cada um tem a própria mão de peças e, logo depois da jogada do jogador humano, faz uma jogada válida, na ordem Lia, Bruno, Kai. Só então a rodada avança.

Os três jogam no nível "médio":
1. Se der para colocar uma peça da mão que capture um objetivo ou que deixe o circuito mais perto da fonte, coloca a melhor delas.
2. Senão, se der para girar uma peça própria e com isso ligar mais casas ao circuito, gira.
3. Senão, passa a vez.

Quando há empate entre jogadas igualmente boas, a escolha é sorteada, sempre com semente: a mesma semente e as mesmas jogadas do jogador humano dão sempre a mesma partida. O histórico da partida mostra o que cada adversário fez.

## Por quê
Hoje a tela avisa que "os adversários estão parados nesta versão: só você joga". O placar deles nunca muda, a classificação final é decidida só pelo jogador humano e a partida não tem disputa. Enquanto não há partidas entre pessoas, a partida precisa de adversários que joguem pelas mesmas regras, para a demonstração mostrar um jogo de verdade e para a colocação, as Fagulhas e o rating da spec 006 terem sentido.

## Critérios de aceitação

### Os adversários jogam
1. **Dado** uma partida em andamento, **quando** faço uma jogada aceita (colocar, girar ou passar), **então** Lia, Bruno e Kai jogam em seguida, nessa ordem, e só depois a rodada avança.
2. **Dado** uma jogada minha recusada (por exemplo, peça solta), **então** nenhum adversário joga e a rodada não muda.
3. Cada adversário tem a própria mão de 5 peças; quando coloca uma, compra outra.
4. Toda jogada de adversário segue as mesmas regras do jogador humano: só coloca peça em casa vazia ligada ao próprio circuito, e só gira peça que existe no tabuleiro.
5. Os pontos e as capturas dos adversários contam como os do jogador humano, e o bônus de +3 por circuito energizado no fim vale para os quatro.

### Estratégia "médio"
6. **Dado** uma peça que captura um objetivo, **então** o adversário a coloca, preferindo o objetivo que vale mais.
7. **Dado** que nenhuma peça captura objetivo, **então** coloca a que deixa o circuito mais perto da fonte, se houver.
8. **Dado** que nenhuma colocação ajuda, **então** gira uma peça própria se isso ligar mais casas ao circuito; senão passa a vez.

### Repetível e visível
9. A mesma semente, com as mesmas jogadas do jogador humano, gera exatamente a mesma partida.
10. O histórico mostra uma linha por jogada de cada adversário, por exemplo "Lia colocou uma curva" ou "Kai passou a vez".
11. Uma partida completa de 12 rodadas termina com a classificação dos quatro jogadores.

### Qualidade
12. As regras dos adversários ficam junto das regras do jogo, sem banco, rede nem relógio.
13. Há testes para: nenhum adversário faz jogada inválida, mesma semente dá a mesma partida, e a partida de 12 rodadas termina com classificação.
14. `pytest`, `ruff` e `mypy` passam.

## Fora do escopo
- Níveis fácil e difícil (só existe o "médio").
- Cartas especiais (Isolante, Ponte, Curto), para os adversários e para o jogador humano.
- Multiplayer em tempo real ou partidas entre pessoas.
- Girar peças de outros jogadores para atrapalhar: o adversário médio só gira as próprias.
- Rating próprio para cada adversário: continuam valendo 1200, como na spec 006.
