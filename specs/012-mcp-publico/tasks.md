# Tarefas — 012 Servidor MCP público do CircuitCrash

**Entrada:** [spec.md](spec.md), [plan.md](plan.md). `[P]` = pode ser feita em paralelo. `[H#]` = história atendida.

## Fase 1 — Resultado sem gravar (H2)
- [x] T001 [H2] `tests/test_mcp_partida.py`: com `Mesa(grava=False)`, o fim traz o resultado com `gravado: false`, a mensagem diz que não grava e o repositório não muda; com a mesa padrão, `gravado: true`
- [x] T002 [H2] `mcps/partida.py`: `Mesa.grava`, campo `gravado` e mensagem do fim; T001 passa

## Fase 2 — Uma mesa por sessão (H3)
- [ ] T003 [H3] `tests/test_mcp_servidor.py`: dois clientes no mesmo servidor têm partidas separadas; as instruções e a docstring de `iniciar_partida` no modo público dizem que não grava; uma partida inteira sem gravar não muda o repositório
- [ ] T004 [H3] `mcps/partida.py`: `Mesas`; `mcps/servidor.py`: tools com `Context`, `criar_servidor(repo, grava=True)` e instruções por modo; T003 e os testes da 011 passam

## Fase 3 — `/mcp` no site (H1)
- [ ] T005 [H1] `tests/test_mcp_publico.py`: com o `lifespan` ligado, um cliente MCP por HTTP em `/mcp` lista as seis tools e consulta o ranking; `/health` continua respondendo
- [ ] T006 [H1] `app.py`: servidor sem gravar sobre o repositório do site, rota `/mcp` e `lifespan`; T005 e `tests/test_paginas.py` passam
- [ ] T007 [H1] Conferir local: `uv run python -m circuitcrash` e `claude mcp add --transport http` para `http://127.0.0.1:8000/mcp`, com ranking e uma partida

## Fase 4 — Publicação e acabamento
- [ ] T008 [P] `README.md`: como conectar ao servidor público e o que muda em relação ao local; `SPEC/2026-10-18-mcp-publico.md` com o status
- [ ] T009 `pytest`, `ruff check`, `ruff format --check` e `mypy` sem erros
- [ ] T010 Depois do merge e do deploy: conectar em `https://circuitcrash.onrender.com/mcp`, consultar o ranking e jogar uma partida até o fim; conferir que `/perfil` do jogador não mudou

## Dependências
Fase 1 → Fase 2 → Fase 3 → Fase 4. Em cada fase, os testes vêm antes da implementação. T009 roda também antes de cada commit.
