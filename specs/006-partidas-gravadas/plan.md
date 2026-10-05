# Plano — 006 Partidas gravadas, Fagulhas e rating

**Spec:** [spec.md](spec.md) · **Data:** 05/10/2026

## Resumo
As regras de Fagulhas e rating ficam num módulo novo, `domain/economia.py`, em Python puro: recebem o jogador, a colocação, os pontos e os ratings dos adversários, e devolvem um `ResultadoPartida`. O contrato `Repositorio` ganha dois métodos: `fagulhas_ganhas_hoje` e `registrar_partida`, que grava a partida e atualiza o jogador numa transação só. `app.py` grava o resultado uma vez, quando a partida termina, e a tela de fim mostra o quadro "Seu resultado". Não há tabela nova: `partidas` e `participacoes` já existem desde a spec 002.

## Contexto técnico
| Item | Escolha |
| --- | --- |
| Regras | `domain/economia.py`, sem banco, rede nem relógio (constituição III) |
| Dados | Dois métodos novos no `Protocol`, implementados em `RepositorioMemoria` e `RepositorioSQL` |
| Transação | `registrar_partida` usa uma única `sessao.begin()`; o jogador é atualizado com `UPDATE ... SET fagulhas = fagulhas + :ganho`, sem ler e regravar o valor |
| Migração | Nenhuma: as tabelas `partidas` e `participacoes` da migração `0001` bastam |
| Testes | pytest; regras puras em `tests/test_economia.py`; gravação com a fixture `repo` (memória e banco); telas em `tests/test_paginas.py` |

## Checagem da constituição
- I Python: ok.
- II Spec antes de código: spec commitada antes; este plano e as tarefas também, antes do código.
- III Regras isoladas: `economia.py` não importa nada de `dados/` e não lê o relógio. O "hoje" do limite diário vem do repositório.
- IV Contrato de dados: dois métodos novos, nenhum alterado. Precisa do aceite do Henrique no PR (ponto 1 da spec).
- V Servidor decide: o navegador não envia colocação, pontos nem Fagulhas; tudo sai do estado da partida guardado no servidor.
- VI Celular: o quadro novo usa as classes que já existem (`painel`, `sobe`, `desce`) e quebra linha a 360 px.
- VII Qualidade: testes novos para cada regra; `ruff` e `mypy` no código novo.

## Estrutura
```text
src/circuitcrash/
├── domain/
│   ├── modelos.py        # + TipoPartida, ResultadoPartida
│   └── economia.py       # novo: recompensas, limite diário, Elo, resultado_da_partida()
├── dados/
│   ├── repositorio.py    # + fagulhas_ganhas_hoje, registrar_partida
│   ├── memoria.py        # implementa os dois métodos; partidas por instância
│   ├── sql.py            # implementa os dois métodos; relógio "agora" injetável
│   └── carga.py          # partidas de exemplo de "hoje" às 00:30, para a partida jogada vir primeiro
├── app.py                # grava ao terminar; RECOMPENSA_COLOCACAO e LIMITE_DIARIO_FAGULHAS vêm de economia
└── web/templates/
    └── _jogo.html        # quadro "Seu resultado" na tela de fim
tests/
├── test_economia.py      # novo: regras puras
├── test_partidas_gravadas.py  # novo: gravação contra memória e banco
└── test_paginas.py       # + partida até o fim pela tela
```

## Regras (`domain/economia.py`)
```python
RECOMPENSA_COLOCACAO = {1: 40, 2: 25, 3: 15, 4: 10}
LIMITE_DIARIO_FAGULHAS = 400
RATING_ADVERSARIO_PADRAO = 1200
K_PROVISORIO = 48
K_NORMAL = 32

def fagulhas_da_colocacao(colocacao: int, tipo: TipoPartida) -> int
def aplicar_limite(ganho: int, ja_ganhas_hoje: int) -> int        # max(0, min(ganho, LIMITE - ja_ganhas))
def esperado(meu_rating: int, rating_adversario: int) -> float    # 1 / (1 + 10 ** ((adv - meu) / 400))
def variacao_elo(meu_rating, meus_pontos, adversarios, provisorio) -> int
def resultado_da_partida(jogador, tipo, colocacao, pontos, objetivos, adversarios, ja_ganhas_hoje) -> ResultadoPartida
```
- `adversarios` é uma sequência de `(rating, pontos)`. Resultado contra cada um: 1 se fiz mais pontos, 0,5 se empatamos, 0 se fiz menos.
- `variacao = round(K / len(adversarios) * soma(resultado - esperado))`, com K pelo `jogador.provisorio`.
- Trava do critério H3.3: o 1º lugar fica com `max(0, variacao)` e o 4º com `min(0, variacao)` (isso só faz diferença quando há empate de pontos com o vizinho).
- Casual: Fagulhas pela metade (`// 2`) e variação 0.
- Colocação fora de 1 a 4 levanta `ValueError`.

`ResultadoPartida` (frozen, em `modelos.py`): `tipo`, `colocacao`, `pontos`, `objetivos`, `rating_antes`, `variacao_rating`, `fagulhas`, `limite_atingido`; propriedades `rating_depois` e `vitoria`.

## Contrato (`dados/repositorio.py`)
```python
def fagulhas_ganhas_hoje(self, jogador_id: str) -> int:
    """Soma das Fagulhas ganhas em partidas que terminaram hoje."""

def registrar_partida(self, jogador_id: str, resultado: ResultadoPartida) -> None:
    """Grava a partida e aplica o resultado ao jogador, tudo ou nada.
    Levanta ValueError se o jogador não existe."""
```

### Memória
- `self._partidas` passa a ser uma cópia por instância de `PARTIDAS` (hoje é o dicionário do módulo, compartilhado).
- `fagulhas_ganhas_hoje`: soma das partidas com `quando == "hoje"`.
- `registrar_partida`: confere o jogador, insere `ResumoPartida(..., "hoje")` no começo da lista e atualiza Fagulhas, rating, partidas, vitórias e objetivos.

### Banco
- `RepositorioSQL(url, hoje=date.today, agora=None)`. Sem `agora`, usa `hoje()` com a hora atual, para que os testes com dia fixo gravem no mesmo dia.
- `fagulhas_ganhas_hoje`: `SUM(participacoes.fagulhas)` com `partidas.terminada_em` entre o início de hoje e o de amanhã; 0 se não houver.
- `registrar_partida`, numa sessão: confere o jogador (`ValueError` se não existe), insere `partidas` (tipo, `iniciada_em` e `terminada_em` = agora) e `participacoes`, e roda o `UPDATE` com os incrementos. Se algo falhar, a transação desfaz tudo (critério 18).
- `carga.py`: as partidas de exemplo passam a terminar às 00:30 menos `i` minutos, em vez de 12:00. Assim uma partida jogada de manhã no dia da apresentação aparece antes das de exemplo de "hoje". A paridade com a memória não muda, porque `quando` só olha a data.

## Tela (`app.py` e `_jogo.html`)
- `_resultados: dict[str, ResultadoPartida]`, ao lado de `_partidas` e com a mesma chave de sessão.
- `_gravar_se_terminou(request, estado)`: se a partida terminou e a chave ainda não está em `_resultados`, calcula com `economia.resultado_da_partida` (colocação e pontos do jogador 0 vêm de `tabuleiro.classificacao`, adversários com `RATING_ADVERSARIO_PADRAO`, objetivos = casas com `capturado_por == 0`), chama `registrar_partida` e guarda. Devolve se gravou agora.
- Chamada em `partida` (GET) e em `_responder_jogo`. Na resposta HTMX em que a partida acabou de ser gravada, o servidor manda `HX-Refresh: true`, para o cabeçalho mostrar as Fagulhas novas (critério H2.5).
- `acao_nova` apaga também a entrada em `_resultados`.
- `_contexto_partida` passa `resultado`. O `_jogo.html` mostra, acima da classificação: "+N Fagulhas" (com "limite do dia atingido" quando for o caso) e "Rating A → B (±V)".
- `RECOMPENSA_COLOCACAO` e `LIMITE_DIARIO_FAGULHAS` saem de `app.py` e passam a vir de `domain/economia.py`; a loja e as regras continuam mostrando os mesmos números.

## Testes
- `tests/test_economia.py`: as quatro colocações e a casual; limite (abaixo, no limite, acima, já estourado); `esperado` simétrico e 0,5 com ratings iguais; 1º sobe e 4º desce com ratings iguais; vencer adversários fortes rende mais; provisório muda mais; empate de pontos; casual não muda rating; colocação inválida.
- `tests/test_partidas_gravadas.py` (fixture `repo`, roda nas duas): `fagulhas_ganhas_hoje` do exemplo (veterano 75, novato 35, nina 0); registrar atualiza o jogador e põe a partida primeiro como "hoje"; soma no limite do dia; jogador inexistente levanta `ValueError` sem gravar nada; o novato sai do provisório e entra no ranking depois de 3 partidas. Só banco: a partida continua lá num `RepositorioSQL` novo sobre o mesmo arquivo.
- `tests/test_paginas.py`: passar a vez até o fim grava uma vez (Fagulhas do cabeçalho sobem uma vez, mesmo abrindo `/partida` de novo); a resposta HTMX do fim traz `HX-Refresh`; o perfil mostra a partida nova; "Jogar de novo" permite gravar outra.

## Decisões
- **Elo de vários adversários, com K dividido pelo número de adversários:** uma partida de 4 vale tanto quanto uma partida de 2, e a variação fica na faixa das partidas de exemplo (±4 a ±18).
- **K maior no provisório (48) em vez de não mexer no rating:** o novato encontra o nível dele mais rápido e o rating não fica parado em 1200 até a 5ª partida.
- **Contadores atualizados por incremento no banco:** uma compra na loja ao mesmo tempo não apaga o ganho da partida, nem o contrário.
- **Gravação na rota e não no tabuleiro:** `tabuleiro.py` não muda, o que facilita o merge com os adversários automáticos.

## Riscos
- **Merge com a spec dos adversários automáticos:** as duas mexem em `app.py` e `_jogo.html`. Mitigação: mudanças pequenas e isoladas (uma função, um bloco no template); quem fizer o merge depois resolve o conflito.
- **Partidas em memória por processo:** com mais de um processo do servidor, a mesma partida poderia ser gravada duas vezes. O Render free roda um processo só, e a demonstração também.
- **Tempo:** congelamento às 23h de 05/10. Se faltar tempo, a ordem das fases já entrega primeiro as regras e a gravação (P1); o quadro na tela (P2) vem por último.
