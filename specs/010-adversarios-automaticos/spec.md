# Spec 010 — Adversários automáticos

**Branch:** `010-adversarios-automaticos` · **Status:** em implementação · **Criada em:** 05/10/2026 · **Dono:** Henrique (regras) · **Origem:** [SPEC/2026-10-05-adversarios-automaticos.md](../../SPEC/2026-10-05-adversarios-automaticos.md)

## Contexto
A spec 001 deixou de propósito "adversários que jogam sozinhos" fora do escopo: na partida de `/partida`, Lia, Bruno e Kai têm peças no tabuleiro, mas nunca jogam. A tela avisa "os adversários estão parados nesta versão" e a colocação final depende só do jogador humano. A spec 006 passou a gravar Fagulhas e rating pela colocação, o que torna a falta de disputa ainda mais visível.

Esta spec faz os três adversários jogarem pelas mesmas regras do jogador humano, no nível "médio", logo depois de cada jogada dele.

Fora do escopo: níveis fácil e difícil, cartas especiais, multiplayer em tempo real, girar peças alheias para atrapalhar e rating próprio para cada adversário.

## Histórias de usuário

### H1 — Os adversários jogam depois de mim (prioridade P1)
Como jogador, quero que Lia, Bruno e Kai joguem depois de mim, para a partida ter disputa.

**Teste independente:** passar a vez e ver no histórico uma linha de cada adversário, e a rodada avançar uma vez.

Critérios de aceitação:
1. **Dado** uma jogada minha aceita (colocar, girar ou passar), **então** Lia, Bruno e Kai jogam em seguida, nessa ordem, e só depois a rodada avança.
2. **Dado** uma jogada minha recusada, **então** nenhum adversário joga e a rodada não muda.
3. Cada adversário tem a própria mão de 5 peças e compra uma nova quando coloca.
4. Toda jogada de adversário é válida pelas regras do jogador humano.
5. Pontos, capturas e o bônus de +3 por circuito energizado no fim valem para os quatro.

### H2 — Os adversários jogam bem o bastante (P1)
Como jogador, quero adversários que busquem objetivos e a fonte, para ganhar deles exigir esforço.

**Teste independente:** montar um tabuleiro em que uma peça da mão de Lia captura um objetivo e ver que ela a coloca.

Critérios de aceitação:
1. **Dado** uma peça que captura um objetivo, **então** o adversário a coloca, preferindo o objetivo que vale mais.
2. **Dado** que nenhuma captura, **então** coloca a peça que deixa o circuito mais perto da fonte.
3. **Dado** que nenhuma colocação ajuda, **então** gira uma peça própria se isso ligar mais casas ao circuito; senão passa.

### H3 — Partida repetível e legível (P2)
Como dupla, queremos que a mesma partida se repita igual nos testes e que o histórico explique o que aconteceu.

Critérios de aceitação:
1. A mesma semente, com as mesmas jogadas do jogador humano, gera a mesma partida.
2. O histórico mostra o que cada adversário fez.
3. Uma partida de 12 rodadas termina com a classificação dos quatro.

## Requisitos funcionais
- **RF-01** Depois de cada jogada aceita do jogador humano, os jogadores 1, 2 e 3 jogam, nessa ordem, antes de a rodada avançar.
- **RF-02** Jogadas possíveis de um adversário: colocar uma peça da mão (em qualquer uma das 4 orientações) numa casa vazia ligada ao próprio circuito; girar 90° uma peça própria; passar.
- **RF-03** Escolha "médio": (a) colocação que mais pontua em capturas; (b) senão, colocação que reduz a menor distância do circuito até a fonte, a maior redução primeiro; (c) senão, giro de peça própria que aumenta o circuito; (d) senão, passar. Empates são sorteados com o sorteio da partida.
- **RF-04** Todo sorteio (peças e desempates) usa a semente da partida.
- **RF-05** O histórico registra uma linha por jogada de adversário.
- **RF-06** No fim, cada jogador com circuito energizado ganha +3.
- **RF-07** As regras ficam em `domain/`, sem banco, rede nem relógio.

## Critérios de sucesso
- **CS-01** Em `/partida`, o placar dos adversários muda ao longo da partida e o histórico mostra as jogadas deles.
- **CS-02** Os testes cobrem jogadas sempre válidas, mesma semente igual partida e partida de 12 rodadas até a classificação.
- **CS-03** `pytest`, `ruff` e `mypy` passam.

## Entidades
- **Adversário automático:** um dos jogadores 1 a 3 da partida, com mão de peças e a estratégia "médio".
- **Jogada:** colocar (peça, orientação, casa), girar (casa) ou passar.
