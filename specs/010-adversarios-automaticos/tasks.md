# Tarefas — 010 Adversários automáticos

**Entrada:** [spec.md](spec.md), [plan.md](plan.md). `[P]` = pode ser feita em paralelo. `[H#]` = história atendida.

## Fase 1 — Estado da partida (H1, H3)
- [ ] T001 [H1] [H3] `domain/tabuleiro.py`: `nova_partida(semente)`, `maos_adversarios` e `_encosta_no_circuito` por jogador

## Fase 2 — Estratégia "médio" (H1, H2)
- [ ] T002 [H1] [H2] `tests/test_adversarios.py`: jogadas sempre válidas, prefere captura, aproxima da fonte, passa quando nada ajuda
- [ ] T003 [H1] [H2] `domain/adversarios.py`: `Jogada`, `jogadas_validas`, `eh_valida`, `escolher_jogada`, `aplicar`, `jogar_adversarios`; T002 passa

## Fase 3 — Turno completo (H1, H3)
- [ ] T004 [H1] [H3] Testes: mesma semente, mesma partida; partida de 12 rodadas termina com classificação; rodada avança uma vez por jogada humana; jogada recusada não aciona os adversários
- [ ] T005 [H1] `domain/tabuleiro.py`: `_fim_do_turno` chama os adversários, histórico de 8 linhas, bônus final para os quatro; T004 passa
- [ ] T006 [H1] `tests/test_paginas.py`: valores do fim de partida com os adversários jogando
- [ ] T007 [H1] `web/templates/partida.html`: troca o aviso dos adversários parados

## Fase 4 — Acabamento
- [ ] T008 [P] `AGENTS.md`: nota sobre a numeração das specs; `SPEC/2026-10-05-adversarios-automaticos.md` com o status
- [ ] T009 `pytest`, `ruff check`, `ruff format --check` e `mypy` sem erros

## Dependências
Fase 1 → Fase 2 → Fase 3 → Fase 4. Em cada fase, os testes vêm antes da implementação.
