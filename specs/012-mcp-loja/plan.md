# Plano — 012 Loja de avatares no servidor MCP

**Spec:** [spec.md](spec.md) · **Data:** 13/10/2026

## Resumo
O cálculo da situação de cada avatar (em uso, possui, exclusivo, pode comprar, faltam) sai de `app.pagina_loja` para uma função pura em `domain/loja.py`, `situacao`. A tela `/loja` passa a chamá-la. Um módulo novo, `mcps/loja.py`, monta a resposta da consulta a partir do repositório e dessa função. `mcps/servidor.py` registra a tool `consultar_loja` com as anotações de leitura (`SO_LEITURA`), e `.claude/settings.json` a coloca em `allow`. Nada muda no contrato `Repositorio`, no banco nem nas dependências.

## Contexto técnico
| Item | Escolha |
| --- | --- |
| SDK | `mcp` 2.3, `MCPServer`, o mesmo da spec 011 |
| Servidor | O `circuitcrash` de `mcps/servidor.py`, com uma tool a mais (sete ao todo) |
| Dados | `Repositorio`: `listar_jogadores` (via `comum.buscar_por_apelido`), `listar_avatares`, `obter_avatar`, `inventario`. Nenhum método de escrita é chamado |
| Regras | `Avatar.preco` e `Raridade` de `domain/modelos.py`; `situacao` nova em `domain/loja.py` |
| Respostas | `TypedDict` como retorno; o SDK gera o esquema de saída |
| Anotações | `SO_LEITURA` de `mcps/comum.py` (`read_only_hint=True`, `idempotent_hint=True`) |
| Permissões | `.claude/settings.json`: `mcp__circuitcrash__consultar_loja` em `permissions.allow` |
| Testes | pytest com a fixture `repo` (memória e SQL); servidor pelo `mcp.Client(servidor)` em processo com `anyio.run` |

## Checagem da constituição
- I Python: ok.
- II Spec antes de código: spec, plano e tarefas commitados antes de qualquer código.
- III Regras isoladas: `situacao` recebe avatar, jogador e inventário prontos, sem banco, rede nem relógio.
- IV Contrato: nenhum método novo ou alterado.
- V Servidor decide: a tool só consulta. Comprar e equipar continuam validados em `loja.comprar` e `loja.equipar`, pelo site.
- VI Celular: sem tela nova; a `/loja` só troca a origem do cálculo e continua igual.
- VII Qualidade: testes da regra, da tool e do servidor; `ruff` e `mypy` estrito.

## Estrutura
```text
.claude/settings.json            # + mcp__circuitcrash__consultar_loja em allow
src/circuitcrash/
├── domain/loja.py               # + Situacao, situacao(avatar, jogador, inventario), faltam(avatar, jogador)
├── app.py                       # pagina_loja usa loja.situacao
└── mcps/
    ├── loja.py                  # novo: consultar_loja(repo, apelido) -> RespostaLoja
    └── servidor.py              # + tool consultar_loja; INSTRUCOES citam a loja
tests/
├── test_loja.py                 # + situacao em cada caso
├── test_mcp_loja.py             # novo: a consulta contra memória e banco
└── test_mcp_servidor.py         # sete tools, quatro de leitura; consulta pelo cliente MCP
```

## `domain/loja.py`
```python
class Situacao(StrEnum):
    EM_USO = "em_uso"
    POSSUI = "possui"
    EXCLUSIVO = "exclusivo"
    COMPRAR = "comprar"
    FALTA = "falta"

def situacao(avatar: Avatar, jogador: Jogador, inventario: set[str]) -> Situacao
def faltam(avatar: Avatar, jogador: Jogador) -> int   # 0 para exclusivo ou quando o saldo cobre
```
- A ordem é a de hoje em `app.pagina_loja`: em uso → possui → exclusivo (`avatar.preco is None`) → comprar (`preco <= fagulhas`) → falta.
- Os valores são as mesmas strings que o template `loja.html` já usa, então o template não muda.
- `app.pagina_loja` troca o `if/elif` por `loja.situacao(...)` e o cálculo de `falta` por `loja.faltam(...)`. `tests/test_paginas.py` garante que a tela não mudou.
- `comprar` e `equipar` não mudam.

## `mcps/loja.py`
```python
class AvatarResumo(TypedDict):     # equipado e possuídos
    id: str
    nome: str
    raridade: str                  # rótulo: "Comum", "Raro", "Épico", "Lendário", "Exclusivo"

class ItemCatalogo(TypedDict):
    id: str
    nome: str
    raridade: str
    preco: int | None              # None para exclusivo
    vendavel: bool                 # False para exclusivo ("não vendável")
    situacao: str                  # em_uso, possui, exclusivo, comprar, falta
    possui: bool
    equipado: bool
    pode_comprar: bool             # situacao == comprar
    faltam: int                    # Fagulhas que faltam; 0 se pode comprar, possui ou é exclusivo

class RespostaLoja(TypedDict):
    encontrado: bool
    apelido: str
    fagulhas: int
    avatar_equipado: AvatarResumo | None
    possuidos: list[AvatarResumo]
    catalogo: list[ItemCatalogo]
    compraveis: int                # quantos itens têm pode_comprar
    mensagem: str

def consultar_loja(repo: Repositorio, apelido: str) -> RespostaLoja
```
- Jogador por `comum.buscar_por_apelido` (sem diferenciar maiúsculas, como no ranking).
- Apelido inexistente: `encontrado=False`, `fagulhas=0`, listas vazias, `avatar_equipado=None`, `mensagem` "Nenhum jogador com o apelido '…'." Nada de exceção.
- Catálogo na ordem de `repo.listar_avatares()`, a mesma da tela.
- `possuidos` na ordem do catálogo (o inventário é um `set`). Um id do inventário sem avatar no catálogo é ignorado.
- `vendavel = avatar.preco is not None`. Preço e "pode comprar" vêm só de `Avatar.preco` e `loja.situacao`: o módulo não compara preço com saldo por conta própria.
- `mensagem`, por exemplo: "lia.ohm tem 900 Fagulhas e usa o Resistor. Pode comprar agora: Faísca, Plug, Chip, Átomo." Sem nenhum comprável: "… Nenhum avatar cabe no saldo; o mais barato à venda custa 150."
- Só métodos de leitura do repositório. Nenhuma chamada a `salvar_jogador`, `adicionar_ao_inventario`, `comprar` ou `equipar`.

## `mcps/servidor.py`
| Tool | Tipo | Docstring (quando usar) |
| --- | --- | --- |
| `consultar_loja(apelido)` | leitura | quando perguntarem quantas Fagulhas um jogador tem, quais avatares ele possui ou o que ele consegue comprar; avisa que não compra nem equipa, e que isso é feito no site |

`INSTRUCOES` ganham uma linha: a loja vende avatares por Fagulhas; os preços são Comum 150, Raro 400, Épico 900 e Lendário 2000 (de `PRECOS`, não escritos à mão); os exclusivos não são vendidos; pelo MCP só se consulta.

## Testes previstos

### `tests/test_loja.py` (regra pura)
- `situacao` devolve cada um dos cinco valores, um caso para cada.
- Preço igual ao saldo vira `COMPRAR`.
- Exclusivo vira `EXCLUSIVO` mesmo com saldo alto, e `POSSUI` ou `EM_USO` quando o jogador o tem.
- `faltam` é 0 para exclusivo e quando o saldo cobre.

### `tests/test_mcp_loja.py` (fixture `repo`: memória e banco)
| Caso | Jogador de exemplo | O que conferir |
| --- | --- | --- |
| Saldo suficiente | `lia.ohm` (900 Fagulhas, usa Resistor, possui Resistor e Onda) | Faísca, Plug, Chip e Átomo vêm com `pode_comprar` (Átomo custa 900, igual ao saldo); Núcleo vem como `falta` com `faltam=1100`; Resistor `em_uso`, Onda `possui`; `compraveis == 4` |
| Sem saldo | `kai_k` (40 Fagulhas) | nenhum `pode_comprar`, `compraveis == 0`; Faísca com `faltam=110`; a mensagem diz que nada cabe no saldo |
| Novato sem avatar | `luma_dev` (60 Fagulhas, sem avatar nem inventário) | `avatar_equipado is None`, `possuidos == []`, catálogo com os 8 avatares, Faísca com `faltam=90` (o mesmo número de `loja.comprar`) |
| Avatar exclusivo | `ninacircuit` (1500, possui a Coroa) e `lia.ohm` | Coroa com `vendavel=False`, `preco=None`, `pode_comprar=False`; para a Nina, `possui=True`; para a Lia, `situacao="exclusivo"` e `faltam=0` |
| Apelido inexistente | `"ninguem"` | `encontrado=False`, mensagem clara, catálogo vazio, sem exceção |
| Maiúsculas e espaços | `"  LIA.OHM "` | encontra o `lia.ohm` |
| Somente leitura | qualquer um | Fagulhas, `avatar_id` e inventário iguais antes e depois da consulta |
| Sem e-mail | todos | nenhum valor da resposta contém `@` |
| Igual à tela | todos os jogadores de exemplo | `situacao` de cada item igual a `loja.situacao` (a função usada pela `/loja`) |

### `tests/test_mcp_servidor.py`
- As sete tools listadas; `consultar_loja` com `read_only_hint=True`, e a docstring com "Use quando".
- `consultar_loja` pelo cliente MCP em processo, sem `is_error`, com `structured_content` igual ao de `mcps.loja.consultar_loja`.
- Apelido inexistente pelo cliente: `is_error` falso.
- `.claude/settings.json`: `allow` com as quatro de leitura, `ask` com as três de escrita.

### `tests/test_paginas.py`
- Os testes atuais da `/loja` continuam passando sem mudança.

## Riscos
- **Saída padrão:** nada de `print` no módulo novo (corrompe o stdio).
- **Mudança em `app.py`:** só troca o `if/elif` da `pagina_loja` por `loja.situacao`. Os testes de página cobrem a tela.
- **Saldo desatualizado:** a resposta é uma foto do momento. Se o jogador gastar Fagulhas no site, a consulta seguinte já mostra o novo saldo, porque nada fica guardado no servidor.
