# Tarefas — 012 Servidor MCP público do CircuitCrash

**Entrada:** [spec.md](spec.md), [plan.md](plan.md). `[P]` = pode ser feita em paralelo. `[H#]` = história atendida.

## Fase 1 — Resultado sem gravar (H2)
- [x] T001 [H2] `tests/test_mcp_partida.py`: com `Mesa(grava=False)`, o fim traz o resultado com `gravado: false`, a mensagem diz que não grava e o repositório não muda; com a mesa padrão, `gravado: true`
- [x] T002 [H2] `mcps/partida.py`: `Mesa.grava`, campo `gravado` e mensagem do fim; T001 passa

## Fase 2 — Partidas por `partida_id` (H3)
Refeita em 18/10 depois da correção da spec: a primeira versão guardava a mesa por sessão MCP, que o protocolo do SDK não tem.
- [x] T003 [H3] `tests/test_mcp_partida.py`: `Mesas` cria ids diferentes e difíceis de adivinhar, acha a mesa pelo id, a resposta traz `partida_id`, id vazio resolve para a última só no modo local, mesas paradas expiram e o limite tira a de uso mais antigo
- [x] T004 [H3] `tests/test_mcp_servidor.py`: no modo público, duas partidas por ids ficam separadas, id ausente ou desconhecido responde sem erro com instrução, a partida inteira não grava, e instruções e descrições dizem que não grava e pedem o `partida_id`; os testes da 011 continuam passando no modo local
- [x] T005 [H3] `mcps/partida.py`: `Mesa.partida_id` e `Mesas`; `mcps/servidor.py`: `criar_servidor(repo, publico=False)`, `partida_id` nas tools e instruções por modo; T003 e T004 passam

## Fase 3 — `/mcp` no site (H1)
- [ ] T006 [H1] `tests/test_mcp_publico.py`: com o `lifespan` ligado, um cliente MCP por HTTP em `/mcp` lista as seis tools, consulta o ranking e joga pelo `partida_id`; `/health` continua respondendo
- [ ] T007 [H1] `app.py`: servidor público sobre o repositório do site, rota `/mcp` (`stateless_http`) e `lifespan`; T006 e `tests/test_paginas.py` passam
- [ ] T008 [H1] Conferir local: `uv run python -m circuitcrash` e `claude mcp add --transport http` para `http://127.0.0.1:8000/mcp`, com ranking e uma partida

## Fase 4 — Publicação e acabamento
- [ ] T009 [P] `README.md`: como conectar ao servidor público e o que muda em relação ao local; `SPEC/2026-10-18-mcp-publico.md` com o status
- [ ] T010 `pytest`, `ruff check`, `ruff format --check` e `mypy` sem erros
- [ ] T011 Depois do merge e do deploy: conectar em `https://circuitcrash.onrender.com/mcp`, consultar o ranking e jogar uma partida até o fim; conferir que `/perfil` do jogador não mudou

## Dependências
Fase 1 → Fase 2 → Fase 3 → Fase 4. Em cada fase, os testes vêm antes da implementação. T010 roda também antes de cada commit.
