# Tarefas — 011 Servidores MCP: ranking, perfil e loja

**Entrada:** [spec.md](spec.md), [plan.md](plan.md). `[P]` = pode ser feita em paralelo. `[H#]` = história atendida.

## Fase 1 — Base comum
- [ ] T001 `pyproject.toml`: dependência `mcp>=2.3.0` (e `uv.lock`)
- [ ] T002 `mcps/comum.py`: `repositorio_do_ambiente`, `buscar_por_apelido` e `SO_LEITURA`

## Fase 2 — Parte 1: ranking (H1)
- [ ] T003 [H1] `tests/test_mcp_ranking.py` com a fixture `repo`: ordem igual a `repo.ranking`, limite padrão, limite ajustado a 1..50, posição de um ranqueado, provisório com partidas que faltam, apelido sem diferenciar maiúsculas, apelido inexistente; pelo cliente MCP em processo: as duas ferramentas listadas como só leitura e uma chamada com resultado estruturado
- [ ] T004 [H1] `mcps/ranking.py`: `ver_ranking`, `posicao_do_jogador`, `criar_servidor`, `main`; T003 passa
- [ ] T005 [H1] `pyproject.toml`: comando `circuitcrash-mcp-ranking`; `.mcp.json` com o servidor de ranking
- [ ] T006 [H1] Conferir à mão: o servidor sobe pelo comando, responde por stdio e os números batem com `/ranking`

## Fase 3 — Parte 2: perfil (H2)
- [ ] T007 [H2] `tests/test_mcp_perfil.py`: números iguais aos do jogador, posição, avatar em uso, 5 recentes, missões, conquistas, sem e-mail, apelido inexistente; cliente em processo
- [ ] T008 [H2] `mcps/perfil.py`; T007 passa
- [ ] T009 [H2] Comando `circuitcrash-mcp-perfil` e entrada no `.mcp.json`

## Fase 4 — Parte 3: loja (H3)
- [ ] T010 [H3] `tests/test_mcp_loja.py`: lista completa, filtro por raridade, raridade inválida, exclusivo sem preço, o que pode comprar para `voltz_br` e `luma_dev`, sem os que já tem; cliente em processo
- [ ] T011 [H3] `mcps/loja.py`; T010 passa
- [ ] T012 [H3] Comando `circuitcrash-mcp-loja` e entrada no `.mcp.json`

## Fase 5 — Acabamento
- [ ] T013 [P] `README.md` (seção dos servidores MCP) e `SPEC/2026-10-12-servidores-mcp.md` com o status
- [ ] T014 Conferir no Claude Code: os três servidores conectados (`/mcp`) e uma pergunta por ferramenta
- [ ] T015 `pytest`, `ruff check`, `ruff format --check` e `mypy` sem erros

## Dependências
Fase 1 → Fase 2 → Fase 3 → Fase 4 → Fase 5. As fases 3 e 4 só dependem da fase 1 e podem ser feitas em qualquer ordem. Em cada fase, os testes vêm antes da implementação. T015 roda também ao fim de cada fase, antes do commit.
