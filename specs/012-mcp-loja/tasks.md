# Tarefas — 012 Loja de avatares no servidor MCP

**Entrada:** [spec.md](spec.md), [plan.md](plan.md). `[P]` = pode ser feita em paralelo. `[H#]` = história atendida.

## Fase 1 — Regra de situação no domínio
- [x] T001 [H1] `tests/test_loja.py`: `situacao` com os cinco valores, preço igual ao saldo, exclusivo com saldo alto e possuído, `faltam`
- [x] T002 [H1] `domain/loja.py`: `Situacao`, `situacao` e `faltam`; T001 passa
- [x] T003 [H1] `app.py`: `pagina_loja` usa `loja.situacao` e `loja.faltam`; `tests/test_paginas.py` passa sem mudança

## Fase 2 — Consulta da loja (H1, H2)
- [x] T004 [H1] [H2] `tests/test_mcp_loja.py` com a fixture `repo`: saldo suficiente (`lia.ohm`), sem saldo (`kai_k`), novato sem avatar (`luma_dev`), avatar exclusivo (Coroa para `ninacircuit` e `lia.ohm`), apelido inexistente, maiúsculas e espaços, somente leitura, sem e-mail, igual à tela
- [x] T005 [H1] [H2] `mcps/loja.py`: `consultar_loja` e os `TypedDict`; T004 passa

## Fase 3 — Servidor e permissões (H2)
- [x] T006 [H2] `tests/test_mcp_servidor.py`: sete tools (quatro de leitura), `consultar_loja` anotada como leitura e com "Use quando", consulta e apelido inexistente pelo cliente MCP, `allow` com as quatro de leitura
- [x] T007 [H1] [H2] `mcps/servidor.py`: tool `consultar_loja` com `SO_LEITURA` e a linha da loja nas `INSTRUCOES`; `.claude/settings.json` com a tool em `allow`; T006 passa
- [x] T008 Conferir por stdio: `uv run circuitcrash-mcp` em memória lista as sete tools, e `consultar_loja` como `lia.ohm` bate com a tela `/loja` — feito em 13/10: sete tools, quatro com `read_only_hint`; `lia.ohm` com Faísca, Plug, Chip e Átomo compráveis e 1100 faltando para o Núcleo. A troca de perfil do site só aceita os dois perfis de demonstração, então a comparação com a tela `/loja` foi feita como `voltz_br` e `luma_dev`: situação e "faltam" iguais nos 8 avatares

## Fase 4 — Acabamento
- [x] T009 [P] `README.md` (seção do servidor MCP) com a tool nova, e `SPEC/2026-10-13-mcp-loja.md` com o status
- [x] T010 `pytest`, `ruff check`, `ruff format --check` e `mypy` sem erros

## Dependências
Fase 1 → Fase 2 → Fase 3 → Fase 4. Em cada fase, os testes vêm antes da implementação. T010 roda também antes de cada commit.
