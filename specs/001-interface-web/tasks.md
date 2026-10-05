# Tarefas — 001 Interface web

**Entrada:** [spec.md](spec.md), [plan.md](plan.md). `[P]` = pode ser feita em paralelo. `[H#]` = história atendida.

## Fase 1 — Base do projeto
- [x] T001 Criar `pyproject.toml` com dependências, ruff, mypy e pytest
- [x] T002 Criar pacote `src/circuitcrash` e `__main__.py` para rodar com `python -m circuitcrash`
- [x] T003 [P] Criar `.gitignore`, `.env.example`, `README.md` e `AGENTS.md`

## Fase 2 — Fundação (bloqueia as histórias)
- [x] T004 Modelos da plataforma em `domain/modelos.py` (Jogador, Avatar, Raridade e preços, Missao, Conquista, ResumoPartida)
- [x] T005 Contrato `Repositorio` em `dados/repositorio.py`
- [x] T006 `RepositorioMemoria` com 6 jogadores, 8 avatares e inventários de exemplo em `dados/memoria.py`
- [x] T007 `criar_app()` com sessão, arquivos estáticos e repositório injetável em `app.py`
- [x] T008 Template base com cabeçalho, carteira, avatar, navegação de desktop e barra inferior no celular
- [x] T009 CSS com as cores das telas de referência e quebras para tablet e celular

## Fase 3 — H1 Partida de demonstração (P1)
- [x] T010 [H1] Testes das regras em `tests/test_tabuleiro.py`: girar, energia, captura, recusa, fim de partida, semente
- [x] T011 [H1] Regras em `domain/tabuleiro.py`: tabuleiro inicial, circuito, captura, colocar, girar, passar, classificação
- [x] T012 [H1] `web/visao.py`: caminhos SVG das peças e rótulos acessíveis
- [x] T013 [H1] `partida.html` e `_jogo.html`: placar, tabuleiro, mão, botões, histórico, resultado final
- [x] T014 [H1] Rotas `/partida/*` com resposta parcial para HTMX e redirecionamento 303 sem HTMX

## Fase 4 — H2 Perfil e H3 Loja (P1)
- [x] T015 [P] [H3] Testes da loja em `tests/test_loja.py`
- [x] T016 [H3] `domain/loja.py`: comprar e equipar com validações
- [x] T017 [H3] `loja.html` com filtros, estados dos cartões e tabela de ganhos; rotas `/loja/comprar` e `/loja/usar`
- [x] T018 [H2] `perfil.html`: identidade, números, progresso até o próximo avatar, partidas, conquistas, inventário e missões

## Fase 5 — H4 e H5 (P2)
- [x] T019 [P] [H4] `inicio.html`, `ranking.html`, `regras.html`
- [x] T020 [H5] Troca de jogador da demonstração (`/jogador`) no cabeçalho e no perfil

## Fase 6 — Acabamento
- [x] T021 Testes das páginas em `tests/test_paginas.py`
- [x] T022 Conferir as telas a 1440 px e a 390 px sem rolagem horizontal
- [x] T023 `ruff check`, `ruff format --check` e `mypy` sem erros

## Dependências
Fase 1 → Fase 2 → (Fase 3 ∥ Fase 4 ∥ Fase 5) → Fase 6.
