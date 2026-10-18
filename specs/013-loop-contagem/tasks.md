# Tarefas — 013 Loop da contagem de linhas

**Entrada:** [spec.md](spec.md), [plan.md](plan.md). `[P]` = pode ser feita em paralelo. `[H#]` = história atendida.

## Fase 1 — Porteiro (H2)
- [x] T001 [H2] `tests/test_loop_conferir.py`: leitura da seção (tabela e blocos), comparação com saídas de `cloc` de exemplo (passou, número errado, bloco errado, data velha), arquivos mudados além do README, queda na contagem e seção ausente
- [x] T002 [H2] `loop/conferir.py`: funções puras + `main` que roda o `cloc` por `CLOC_PL`, `git status` e `git show HEAD:README.md`; saídas 0, 1 e 2; T001 passa; `mypy` também no `conferir.py`

## Fase 2 — Desenho do loop (H1)
- [x] T003 [H1] `loop/PROMPT.md`: tarefa, gatilho e justificativa, critério de parada, quando parar e chamar a dupla, o que não tocar e como se conferir
- [x] T004 [H1] `loop/permissoes.json`: allow e deny da volta
- [x] T005 [H1] `loop/ESTADO.md` com o modelo de entrada; commit do loop antes da primeira volta

## Fase 3 — Voltas (H3)
- [x] T006 [H3] Volta 1: `claude -p` numa sessão nova; porteiro roda `conferir.py` e `pytest`, anota em `ESTADO.md` e decide — 18/10 19:07, PASSOU, decisão: parar
- [x] T007 [H3] Voltas 2 e 3, se a decisão for tentar de novo — não precisou: a volta 1 passou
- [x] T008 [H3] `diario/2026-10-13.md`: onde o loop parou, o que deu errado e o que automatizar primeiro

## Fase 4 — Acabamento
- [x] T009 [P] `README.md`: linha sobre a pasta `loop/` na tabela de estrutura; `SPEC/2026-10-18-loop-contagem.md` com o status
- [x] T010 `pytest`, `ruff check`, `ruff format --check` e `mypy` sem erros

## Dependências
Fase 1 → Fase 2 → Fase 3 → Fase 4. T002 e o commit do loop vêm antes da primeira volta, porque o `cloc` só conta arquivos versionados.
