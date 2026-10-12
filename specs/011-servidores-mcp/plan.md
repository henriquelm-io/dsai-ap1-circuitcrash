# Plano — 011 Servidores MCP: ranking, perfil e loja

**Spec:** [spec.md](spec.md) · **Data:** 12/10/2026

## Resumo
Um pacote novo, `circuitcrash/mcps/`, com um módulo por servidor. Em cada módulo, as consultas são funções comuns que recebem o `Repositorio` e devolvem dicionários tipados; o servidor MCP só embrulha essas funções como ferramentas. Assim, os testes chamam as funções direto com a fixture `repo` (memória e banco), e um teste a mais conversa com o servidor por um cliente MCP em memória. Cada servidor tem um comando próprio no `pyproject.toml` e uma entrada no `.mcp.json` da raiz, que o Claude Code lê ao abrir o projeto.

A entrega é feita em partes, uma por servidor: ranking primeiro, depois perfil e loja.

## Contexto técnico
| Item | Escolha |
| --- | --- |
| SDK | `mcp` 2.3 (SDK oficial em Python). Na versão 2, o antigo `FastMCP` se chama `MCPServer` (`mcp.server.mcpserver`) |
| Transporte | stdio: o Claude Code inicia o processo e conversa pela entrada e saída padrão |
| Dados | `criar_repositorio(url_do_banco())` depois de `carregar_env()`, como o site; sem banco, memória |
| Respostas | `TypedDict` como tipo de retorno: o SDK gera o esquema de saída e devolve o resultado estruturado |
| Só leitura | Toda ferramenta é marcada com `ToolAnnotations(read_only_hint=True)` e não chama nenhum método que grava |
| Testes | pytest; consultas com a fixture `repo`; servidor por `mcp.Client(servidor)` em processo, com `anyio` |

## Checagem da constituição
- I Python: ok; sem JavaScript.
- II Spec antes de código: spec commitada antes; plano e tarefas também, antes do código.
- III Regras isoladas: nada muda em `domain/`. As consultas ficam em `mcps/`, fora do domínio.
- IV Contrato de dados: nenhum método novo ou alterado. A busca por apelido percorre `listar_jogadores()`.
- V Servidor decide: as ferramentas só leem; compra e troca de avatar continuam só nas rotas validadas do site.
- VI Celular: não se aplica (sem tela nova).
- VII Qualidade: testes para cada ferramenta; `ruff` e `mypy` estrito no código novo.

## Estrutura
```text
.mcp.json                     # os servidores para o Claude Code (um por parte)
src/circuitcrash/mcps/
├── __init__.py
├── comum.py                  # repositório do ambiente, busca por apelido
├── ranking.py                # parte 1: ver_ranking, posicao_do_jogador, criar_servidor, main
├── perfil.py                 # parte 2: perfil_do_jogador
└── loja.py                   # parte 3: listar_avatares, o_que_posso_comprar
tests/
├── test_mcp_ranking.py
├── test_mcp_perfil.py
└── test_mcp_loja.py
```

## Comum (`mcps/comum.py`)
```python
def repositorio_do_ambiente() -> Repositorio          # carregar_env(); criar_repositorio(url_do_banco())
def buscar_por_apelido(repo, apelido) -> Jogador | None  # strip + casefold sobre listar_jogadores()
SO_LEITURA = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
```

## Parte 1 — Ranking (`mcps/ranking.py`)
```python
LIMITE_PADRAO = 10
LIMITE_MAXIMO = 50

class LinhaRanking(TypedDict): posicao, apelido, rating, partidas, vitorias, taxa_vitoria
class Ranking(TypedDict): jogadores: list[LinhaRanking]; total: int
class Posicao(TypedDict): encontrado, apelido, posicao (int | None), rating, partidas, provisorio, partidas_para_entrar, mensagem

def ver_ranking(repo, limite=LIMITE_PADRAO) -> Ranking          # limite ajustado a 1..50; repo.ranking(limite)
def posicao_do_jogador(repo, apelido) -> Posicao                # posição como em /perfil: índice em repo.ranking(1000)
def criar_servidor(repo: Repositorio | None = None) -> MCPServer
def main() -> None                                               # criar_servidor().run("stdio")
```
- `partidas_para_entrar = max(0, PARTIDAS_PARA_RANKING - partidas)`.
- Apelido inexistente: `encontrado=False`, demais campos zerados e mensagem "Nenhum jogador com o apelido ...".
- O repositório é criado uma vez em `criar_servidor`, quando não é passado (os testes passam o deles).
- Comando: `circuitcrash-mcp-ranking = "circuitcrash.mcps.ranking:main"`.

## Parte 2 — Perfil (`mcps/perfil.py`)
`perfil_do_jogador(repo, apelido)` devolve os números do jogador (sem e-mail), a posição como na parte 1, o nome do avatar em uso, `partidas_recentes(id, 5)`, `missoes_do_dia(id)` e `conquistas(id)`. Comando `circuitcrash-mcp-perfil`.

## Parte 3 — Loja (`mcps/loja.py`)
- `listar_avatares(repo, raridade="todos")`: nome, raridade, preço (`None` = exclusivo, "não vendido") e descrição; raridade inválida devolve a lista de valores aceitos.
- `o_que_posso_comprar(repo, apelido)`: Fagulhas, `pode_comprar` e `faltam` (com quanto falta), do mais barato para o mais caro, sem os que ele tem e sem exclusivos.
- Comando `circuitcrash-mcp-loja`.

## `.mcp.json`
```json
{ "mcpServers": { "circuitcrash-ranking": { "command": "uv", "args": ["run", "circuitcrash-mcp-ranking"] } } }
```
Os servidores rodam na pasta do projeto, então leem o mesmo `.env` e o mesmo `circuitcrash.db` do site. Cada parte acrescenta a sua entrada.

## Riscos
- **Saída padrão:** no stdio, qualquer `print` corrompe o protocolo. Os módulos não imprimem nada; avisos vão para o stderr pelo `logging`.
- **SDK novo (2.x):** a API mudou em relação aos tutoriais da versão 1. A dependência fica em `mcp>=2.3.0`.
- **Smart App Control:** o `mcp` traz dependências compiladas (`pydantic-core`, `rpds-py`, `pywin32`). Se alguma for bloqueada, registrar no `AGENTS.md` como foi feito com o `ast-serialize`.
