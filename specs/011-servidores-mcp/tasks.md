# Tarefas — 011 Servidor MCP do CircuitCrash: partida e ranking

**Entrada:** [spec.md](spec.md), [plan.md](plan.md). `[P]` = pode ser feita em paralelo. `[H#]` = história atendida.

## Fase 1 — Base comum (feita na primeira versão)
- [x] T001 `pyproject.toml`: dependência `mcp>=2.3.0` (e `uv.lock`)
- [x] T002 `mcps/comum.py`: `repositorio_do_ambiente`, `buscar_por_apelido` e `SO_LEITURA`

## Fase 2 — Consultas de ranking (H1, feita na primeira versão)
- [x] T003 [H1] `tests/test_mcp_ranking.py` com a fixture `repo`: ordem igual a `repo.ranking`, limites, posição de um ranqueado, provisório, apelido sem diferenciar maiúsculas, apelido inexistente
- [x] T004 [H1] `mcps/ranking.py`: `ver_ranking` e `posicao_do_jogador`
- [x] T005 [H1] Conferido em 12/10 por stdio (top 5 igual a `/ranking`) e no Claude Code por Severino (`/mcp` conectado, top 5 e posição do `luma_dev`), ainda como servidor `circuitcrash-ranking`

## Fase 3 — Resultado da partida no domínio
- [x] T006 `tests/test_economia.py`: `resultado_da_demo` com a partida de demonstração terminada (colocação, pontos, objetivos, Fagulhas e rating iguais ao cálculo do site)
- [x] T007 `domain/economia.py`: `resultado_da_demo`; `app.py` usa a função; T006 e `tests/test_paginas.py` passam

## Fase 4 — Partida pelo MCP (H2)
- [x] T008 [H2] `tests/test_mcp_partida.py` com a fixture `repo`: sem partida, iniciar (apelido inexistente e válido), ver (rodada, placar, mão, casas ocupadas, jogadas válidas), jogada válida passa a vez, jogada recusada não gasta a vez nem gira a peça, peça fora da mão, girar peça do tabuleiro, passar, fim grava uma vez com o resultado na resposta e no repositório, iniciar de novo descarta, sem e-mail
- [x] T009 [H2] `mcps/partida.py`: `Mesa`, `iniciar`, `ver`, `jogar`, `passar`; T008 passa

## Fase 5 — Servidor único e permissões (H1, H2, H3)
- [x] T010 [H3] `tests/test_mcp_servidor.py`: as seis tools listadas, leitura com `read_only_hint` e escrita sem, docstrings com "Use quando"; uma partida inteira pelo cliente MCP em processo
- [x] T011 [H1] [H2] `mcps/servidor.py` com as seis tools e `main`; `ranking.py` sem servidor próprio; `comum.py` com `ESCRITA`; T010 passa
- [x] T012 [H3] `pyproject.toml`: comando `circuitcrash-mcp` no lugar de `circuitcrash-mcp-ranking`; `.mcp.json` com o servidor `circuitcrash`; `.claude/settings.json` com `allow` (leitura), `ask` (escrita) e `enabledMcpjsonServers`
- [x] T013 Conferir por stdio: o servidor sobe pelo comando e lista as seis tools — feito em 12/10 com `uv run circuitcrash-mcp` em memória: três de leitura, três de escrita, e `iniciar_partida` como `luma_dev` com 16 jogadas válidas

## Fase 6 — Agente e diário (H3)
- [ ] T014 [H3] Rodar a tarefa com `claude -p` em modo headless num SQLite temporário: primeiro sem liberar a escrita (o `ask` deve barrar), depois liberando as tools de escrita para aquela execução
- [ ] T015 [H3] `diario/2026-10-08.md`: tarefa, tools chamadas em ordem, onde o agente errou, resultado conferido no banco e a perna da tríade que o servidor abre

## Fase 7 — Acabamento
- [ ] T016 [P] `README.md` (seção do servidor MCP) e `SPEC/2026-10-12-servidores-mcp.md` com o status
- [ ] T017 `pytest`, `ruff check`, `ruff format --check` e `mypy` sem erros

## Dependências
Fase 3 → Fase 4 → Fase 5 → Fase 6 → Fase 7. Em cada fase, os testes vêm antes da implementação. T017 roda também antes de cada commit.
