# Plano — 011 Servidor MCP do CircuitCrash: partida e ranking

**Spec:** [spec.md](spec.md) · **Data:** 12/10/2026 (corrigido no mesmo dia, junto com a spec)

## Resumo
O pacote `circuitcrash/mcps/` ganha um servidor único, `servidor.py`, com seis tools. As consultas de ranking (`ranking.py`, já feitas) continuam como estão; as ações da partida ficam em `partida.py`, que só chama as regras de `domain/tabuleiro.py`. O cálculo do resultado da partida de demonstração sai de `app.py` para `domain/economia.py` (`resultado_da_demo`), e o site e o MCP passam a usar a mesma função. As permissões ficam em `.claude/settings.json` (versionado): leitura em `allow`, escrita em `ask`. O agente roda a tarefa em modo headless (`claude -p`), e o rastro das tools vai para `diario/2026-10-08.md`.

## Contexto técnico
| Item | Escolha |
| --- | --- |
| SDK | `mcp` 2.3. Na versão 2, o `FastMCP` virou `MCPServer` (`mcp.server.mcpserver`) |
| Transporte | stdio, iniciado pelo Claude Code a partir do `.mcp.json` |
| Dados | `Repositorio` do `.env`, como o site; sem banco, memória |
| Estado da partida | Um objeto `Mesa` no processo do servidor: estado do tabuleiro, jogador e resultado gravado (ou `None`) |
| Respostas | `TypedDict` como retorno; o SDK gera o esquema de saída |
| Anotações | Leitura: `read_only_hint=True`. Escrita: `read_only_hint=False`, `destructive_hint=False` (só acrescenta), `idempotent_hint=False` |
| Permissões | `.claude/settings.json`: `permissions.allow` com `mcp__circuitcrash__<tool>` de leitura, `permissions.ask` com as de escrita, `enabledMcpjsonServers: ["circuitcrash"]` |
| Testes | pytest com a fixture `repo`; servidor pelo `mcp.Client(servidor)` em processo com `anyio.run` |

## Checagem da constituição
- I Python: ok.
- II Spec antes de código: spec corrigida e commitada antes; este plano e as tarefas também.
- III Regras isoladas: `resultado_da_demo` vai para `domain/economia.py` sem banco, rede nem relógio (o "já ganhas hoje" vem de fora). O MCP não reimplementa regra: a lista de jogadas válidas é calculada tentando cada jogada numa cópia do estado com `tabuleiro.jogar_na_casa`.
- IV Contrato: nenhum método novo ou alterado.
- V Servidor decide: o agente só manda intenções (peça, giros, casa); o domínio valida.
- VI Celular: sem tela nova.
- VII Qualidade: testes de cada tool; `ruff` e `mypy` estrito.

## Estrutura
```text
.mcp.json                       # servidor "circuitcrash" (troca o "circuitcrash-ranking")
.claude/settings.json           # novo: allow (leitura) e ask (escrita)
diario/2026-10-08.md            # novo: registro do agente usando o servidor
src/circuitcrash/
├── domain/economia.py          # + resultado_da_demo(jogador, estado, ja_ganhas_hoje)
├── app.py                      # _gravar_se_terminou usa resultado_da_demo
└── mcps/
    ├── comum.py                # + ESCRITA (anotações das tools de escrita)
    ├── ranking.py              # ver_ranking, posicao_do_jogador (sem servidor próprio)
    ├── partida.py              # novo: Mesa, iniciar, ver, jogar, passar
    └── servidor.py             # novo: criar_servidor com as 6 tools, main
tests/
├── test_economia.py            # + resultado_da_demo
├── test_mcp_ranking.py         # só as funções de ranking
├── test_mcp_partida.py         # novo
└── test_mcp_servidor.py        # novo: tools, anotações e uma partida pelo cliente MCP
```

## `domain/economia.py`
```python
def resultado_da_demo(jogador: Jogador, estado: EstadoPartida, ja_ganhas_hoje: int,
                      tipo: TipoPartida = TipoPartida.RANQUEADA) -> ResultadoPartida
```
O mesmo cálculo que hoje está em `app._gravar_se_terminou`: colocação e pontos de "Você" (índice 0) pela `classificacao`, adversários com `RATING_ADVERSARIO_PADRAO`, objetivos capturados por 0. `app.py` passa a chamar esta função; os testes de `test_paginas.py` garantem que o site não mudou.

## `mcps/partida.py`
```python
@dataclass
class Mesa:  # a partida em andamento no servidor
    estado: EstadoPartida | None = None
    jogador_id: str | None = None
    resultado: ResultadoPartida | None = None

def iniciar(repo, mesa, apelido) -> RespostaPartida     # nova_partida(); descarta a anterior
def ver(mesa) -> RespostaPartida                        # leitura
def jogar(repo, mesa, peca, giros, linha, coluna) -> RespostaPartida
def passar(repo, mesa) -> RespostaPartida
```
- `RespostaPartida`: `ativa`, `apelido`, `aceita`, `mensagem`, `rodada`, `max_rodadas`, `rodadas_restantes`, `terminou`, `placar` (jogador, pontos, energizado), `mao` (índice, formato, saídas), `casas` (só as ocupadas: linha, coluna, tipo, saídas, dono, objetivo, capturado por), `jogadas_validas` (peça, giros, linha, coluna, saídas resultantes) e `resultado` (colocação, pontos, Fagulhas, limite atingido, rating antes e depois) quando gravado.
- `jogar`: peça fora da mão é recusada. Seleciona a peça e gira `giros % 4` vezes; se o domínio recusa, as saídas da peça voltam ao que eram, para a próxima tentativa partir da mesma orientação mostrada em `ver_partida`. Numa casa com peça, o domínio gira a peça do tabuleiro (peça e giros são ignorados).
- Jogadas válidas: casas vazias vizinhas do circuito de "Você"; para cada peça e giro com saídas diferentes, `jogar_na_casa` numa `deepcopy` do estado.
- Ao terminar (`estado.terminou`) e com `resultado is None`: `resultado_da_demo` com o jogador relido do repositório e `repo.registrar_partida`, uma vez.
- Sem partida: `ativa=False`, mensagem "Nenhuma partida em andamento. Use iniciar_partida."

## `mcps/servidor.py`
| Tool | Tipo | Docstring (quando usar) |
| --- | --- | --- |
| `ver_ranking(limite=10)` | leitura | quando perguntarem quem lidera ou pedirem a classificação |
| `posicao_do_jogador(apelido)` | leitura | quando perguntarem a posição ou o rating de um jogador específico; antes de iniciar uma partida, para conferir o apelido |
| `ver_partida()` | leitura | antes de cada jogada, para ver mão, tabuleiro e jogadas válidas; e para consultar o placar |
| `iniciar_partida(apelido)` | escrita | quando pedirem para jogar uma partida como um jogador; descarta a partida em andamento |
| `jogar_peca(peca, giros, linha, coluna)` | escrita | na vez do jogador, para colocar uma peça da mão (de preferência uma das jogadas válidas) |
| `passar_vez()` | escrita | quando não houver jogada válida ou útil |

As `instructions` do servidor resumem as regras: tabuleiro 7×7 com linhas e colunas de 0 a 6, base de "Você" em (0,0), fonte em (3,3), saídas N/E/S/W, giro de 90° no sentido horário, partida até a rodada 12, objetivos valem pontos quando capturados por um circuito ligado à fonte.

Comando: `circuitcrash-mcp = "circuitcrash.mcps.servidor:main"` (substitui `circuitcrash-mcp-ranking`).

## Diário (headless)
1. Rodar `claude -p` na pasta do projeto, com `--output-format stream-json --verbose`, pedindo: "Jogue uma partida do CircuitCrash como luma_dev, tentando ficar o mais alto possível, e no fim me diga a colocação e quanto o rating e as Fagulhas mudaram."
2. Primeira rodada sem liberar a escrita: no modo headless o `ask` não tem a quem perguntar, então a escrita deve ser negada. Isso mostra o `ask` funcionando.
3. Segunda rodada liberando as tools de escrita só para aquela execução (`--allowedTools`), registrando no diário que a licença foi dada pela linha de comando.
4. Extrair do rastro as tools chamadas, em ordem, as jogadas recusadas e a resposta final; conferir o resultado no banco.

O banco usado é um SQLite temporário com a carga do exemplo (`DATABASE_URL` na linha de comando), para não mexer no `circuitcrash.db` de quem roda.

## Riscos
- **Saída padrão:** nada de `print` nos módulos do servidor (corrompe o stdio).
- **Muitas licenças:** a partida tem 7 jogadas (rodadas 6 a 12), e cada uma pede licença no modo interativo. É o efeito pedido pelo `ask`.
- **Mudança em `app.py`** (área do Henrique): só troca o cálculo inline por `resultado_da_demo`, coberto pelos testes de página.
