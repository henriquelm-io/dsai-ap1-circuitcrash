# Tarefas — 002 Banco de dados

**Entrada:** [spec.md](spec.md), [plan.md](plan.md). `[P]` = pode ser feita em paralelo. `[H#]` = história atendida.

## Fase 1 — Dependências e configuração
- [x] T001 `uv add sqlalchemy alembic python-dotenv` e extra opcional `postgres` com `psycopg[binary]` no `pyproject.toml`; conferir que `uv run mypy` e `uv run pytest` continuam passando
- [x] T002 [H3] `dados/config.py`: `url_do_banco()` lê `DATABASE_URL` (vazia vira `None`) e troca `postgresql://` por `postgresql+psycopg://`; `carregar_env()` lê o `.env` se existir
- [x] T003 [P] [H3] `.env.example` com `DATABASE_URL=sqlite:///circuitcrash.db` e comentário com a URL do PostgreSQL
- [x] T004 [H3] `__main__.py`: passar `env_file=".env"` ao `uvicorn.run` quando o arquivo existir

## Fase 2 — Tabelas e migração (bloqueia as histórias)
- [x] T005 [H1] [H4] `dados/tabelas.py`: `Base` e as nove tabelas do plano, com `ordem`, `google_sub` único e nulo, `CHECK (fagulhas >= 0)`, `CHECK` de raridade, tipo e colocação, e `PRAGMA foreign_keys=ON` no SQLite
- [x] T006 `alembic.ini` e `migracoes/env.py` usando `carregar_env()`, `url_do_banco()` e `Base.metadata`
- [x] T007 [H1] [H4] Migração `0001_tabelas_iniciais` gerada com autogenerate e revisada à mão; `uv run alembic upgrade head` cria um `circuitcrash.db` vazio

## Fase 3 — H1 e H3: repositório com banco (P1)
- [x] T008 [H3] `tests/conftest.py`: fixture `repo` parametrizada (`memoria`, `sql` com SQLite em `tmp_path`, migrado e carregado)
- [x] T009 [H3] `tests/test_loja.py` usando a fixture `repo`; o teste de compra salva o novato e relê do repositório antes de conferir
- [x] T010 [H1] `tests/test_banco.py`: paridade de todos os métodos do contrato com a memória, persistência após reabrir o arquivo, Fagulhas negativas recusadas, `google_sub` repetido recusado
- [x] T011 [H1] `dados/sql.py`: `RepositorioSQL` com os onze métodos do contrato, devolvendo dataclasses de `domain/modelos.py`
- [x] T012 [H3] `dados/fabrica.py`: `criar_repositorio(url)` e teste da escolha pela URL
- [x] T013 [H3] `app.py`: `criar_app()` usa `criar_repositorio(url_do_banco())` quando nenhum repositório é passado

## Fase 4 — H2: carga de exemplo (P1)
- [x] T014 [H2] `dados/carga.py`: migra, carrega avatares, jogadores, inventários, partidas, missões e conquistas na ordem de `dados/memoria.py`; não duplica; `--recriar` apaga e carrega de novo
- [x] T015 [H2] Testes da carga em `tests/test_banco.py`: rodar duas vezes não duplica; `--recriar` volta ao estado inicial
- [x] T016 [P] [H2] `tests/test_paginas.py`: as telas abrem com `RepositorioSQL`

## Fase 5 — Acabamento
- [x] T017 [P] `README.md` e `docs/banco-de-dados.md`: criar o banco, carregar o exemplo, recriar, usar PostgreSQL; `AGENTS.md` com os comandos novos
- [x] T018 Conferir à mão: comprar na loja, reiniciar o servidor, ver o avatar no perfil (CS-03)
- [x] T019 `pytest`, `ruff check`, `ruff format --check` e `mypy` sem erros
- [ ] T020 (opcional) Rodar com PostgreSQL via Docker: `uv sync --extra postgres`, migrar, carregar e abrir as telas — não feita: Docker não instalado na máquina do parceiro; o driver `psycopg` 3.3.6 instala e carrega

## Dependências
Fase 1 → Fase 2 → Fase 3 → Fase 4 → Fase 5. Dentro da Fase 3, os testes (T008–T010) vêm antes da implementação (T011–T013). T014 depende de T011, e os testes `sql` da fixture só passam depois de T014.
