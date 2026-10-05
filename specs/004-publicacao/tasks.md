# Tarefas — 004 Publicação

**Entrada:** [spec.md](spec.md), [plan.md](plan.md). `[P]` = pode ser feita em paralelo. `[H#]` = história atendida.

## Fase 1 — Repositório
- [ ] T001 [P] [H3] `.gitignore`: ignorar `.venv-*/`
- [ ] T002 [H1] [H2] [H3] `render.yaml`: Web Service free na `main` com deploy automático, build com `uv sync --frozen --no-dev`, início com a carga `--recriar` antes do servidor, `HOST=0.0.0.0`, `RELOAD=0`, `DATABASE_URL` SQLite, `SECRET_KEY` gerada pelo Render, `healthCheckPath: /health`
- [ ] T003 [H2] [H3] Validar o comando de início localmente com um `DATABASE_URL` temporário: a carga roda, o uvicorn sobe em `0.0.0.0` e `/health` responde
- [ ] T004 [H3] Rodar `pytest`, `ruff check`, `ruff format --check` e `mypy`

## Fase 2 — Publicação (depois do merge na `main`)
- [ ] T005 [H1] Criar o serviço no Render pelo Blueprint (`render.yaml`) e conferir no navegador do computador e do celular todas as telas por HTTPS
- [ ] T006 [H2] Reiniciar o serviço e conferir que a troca de avatar some e o exemplo volta
- [ ] T007 [P] [H3] `README.md`: URL pública e o passo a passo para refazer a publicação do zero
