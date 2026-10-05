# Tarefas — 006 Partidas gravadas, Fagulhas e rating

**Entrada:** [spec.md](spec.md), [plan.md](plan.md). `[P]` = pode ser feita em paralelo. `[H#]` = história atendida.

## Fase 1 — Regras puras (H2, H3)
- [x] T001 [H2] [H3] `tests/test_economia.py`: testes das recompensas por colocação, casual, limite diário, `esperado`, Elo (1º sobe, 4º desce, adversários fortes rendem mais, provisório muda mais, empate de pontos, casual sem rating) e colocação inválida
- [x] T002 [H2] [H3] `domain/modelos.py`: `TipoPartida` e `ResultadoPartida` (com `rating_depois` e `vitoria`)
- [x] T003 [H2] [H3] `domain/economia.py`: constantes, `fagulhas_da_colocacao`, `aplicar_limite`, `esperado`, `variacao_elo` e `resultado_da_partida`; T001 passa

## Fase 2 — Gravação no repositório (H1)
- [x] T004 [H1] `tests/test_partidas_gravadas.py` com a fixture `repo`: Fagulhas de hoje do exemplo, registrar atualiza o jogador e as recentes, soma no limite, jogador inexistente não grava nada, novato entra no ranking; só banco: persiste num `RepositorioSQL` novo
- [x] T005 [H1] `dados/repositorio.py`: `fagulhas_ganhas_hoje` e `registrar_partida` no `Protocol`
- [x] T006 [H1] `dados/memoria.py`: partidas por instância e os dois métodos
- [x] T007 [H1] `dados/sql.py`: relógio `agora` injetável e os dois métodos, `registrar_partida` numa transação com `UPDATE` por incremento
- [x] T008 [H1] `dados/carga.py`: partidas de exemplo às 00:30 menos `i` minutos; testes de paridade continuam passando

## Fase 3 — Fim de partida na tela (H1, H2, H4)
- [x] T009 [H1] [H4] `tests/test_paginas.py`: partida até o fim grava uma vez, `HX-Refresh` no fim via HTMX, perfil mostra a partida, "Jogar de novo" grava outra
- [x] T010 [H1] [H2] `app.py`: constantes vindas de `economia`, `_resultados`, `_gravar_se_terminou`, `HX-Refresh` e limpeza em `acao_nova`
- [x] T011 [H4] `web/templates/_jogo.html`: quadro "Seu resultado" com Fagulhas, aviso de limite e rating antes → depois

## Fase 4 — Acabamento
- [ ] T012 [P] `README.md` (demonstração), `docs/banco-de-dados.md` e `SPEC/2026-10-05-partidas-gravadas.md` com o status
- [ ] T013 Conferir à mão com o banco: jogar até o fim como `voltz_br` e `luma_dev`, ver cabeçalho, perfil e ranking; reiniciar o servidor e conferir de novo; tela a 390 px
- [ ] T014 `pytest`, `ruff check`, `ruff format --check` e `mypy` sem erros

## Dependências
Fase 1 → Fase 2 → Fase 3 → Fase 4. Em cada fase, os testes vêm antes da implementação. T007 depende de T005; T010 depende de T003 e T005.
