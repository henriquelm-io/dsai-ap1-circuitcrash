# Instruções para agentes de IA

Leia antes de qualquer tarefa: `.specify/memory/constitution.md` e a pasta da spec em que vai trabalhar (`specs/NNN-nome/`).

## Regra de ouro
Nada de código sem `spec.md`, `plan.md` e `tasks.md` da funcionalidade. Se a tarefa não está no `tasks.md`, pare e pergunte.

## Comandos
| Para | Comando |
| --- | --- |
| Instalar | `uv sync` |
| Rodar | `uv run python -m circuitcrash` (porta 8000) |
| Testar | `uv run pytest` |
| Lint | `uv run ruff check` e `uv run ruff format --check` |
| Tipos | `uv run mypy` |
| Banco: migrar | `uv run alembic upgrade head` |
| Banco: carregar exemplo | `uv run python -m circuitcrash.dados.carga` (`--recriar` apaga e carrega de novo) |

Rode os quatro de qualidade antes de cada commit.

## Onde mexer
- Regras do jogo e da loja: `src/circuitcrash/domain/`. Python puro: sem banco, rede, relógio ou sorteio sem semente.
- Acesso a dados: implemente o `Protocol` de `src/circuitcrash/dados/repositorio.py`. Não altere a assinatura sem combinar com a dupla. Há duas implementações, `RepositorioMemoria` e `RepositorioSQL`; os testes com a fixture `repo` (`tests/conftest.py`) rodam contra as duas.
- Banco: tabelas em `dados/tabelas.py`, migrações em `migracoes/` (Alembic). Nunca altere uma migração já na `main`; crie outra. Guia em `docs/banco-de-dados.md`.
- Telas: `src/circuitcrash/web/templates/` e `web/static/css/app.css`. Toda tela precisa funcionar a 390 px de largura e sem HTMX.
- Rotas: `src/circuitcrash/app.py`. A validação fica em `domain/`, nunca no template.

## Git
- Uma branch por spec: `NNN-nome`.
- Commits em português, no imperativo: `feat: adiciona loja de avatares`.
- Nunca commite `.env` nem credenciais.

## Ambiente Windows
- O Smart App Control do Windows pode bloquear binários (`.pyd`/`.dll`) publicados há pouco tempo, porque ainda não têm reputação. O sintoma é `ImportError: DLL load failed ... Uma política de Controle de Aplicativo bloqueou este arquivo`.
- Em 04/10/2026 isso aconteceu com o `ast-serialize` 0.12.1 (publicado em 03/10/2026), o parser nativo do `mypy` 2.4.0: `uv run mypy` dava `INTERNAL ERROR`. Por isso o grupo `dev` fixa `ast-serialize<0.12.1`, e o `mypy` continua na 2.4.0.
- Quando a 0.12.1 (ou uma mais nova) deixar de ser bloqueada, dá para tirar a trava com `uv remove --dev ast-serialize`. Rode `uv run mypy` para confirmar.
- Em 04/10/2026 as extensões compiladas do SQLAlchemy 2.1.3 e do `psycopg-binary` 3.3.6 carregaram sem bloqueio. Se forem bloqueadas, use `DISABLE_SQLALCHEMY_CEXT_RUNTIME=1` (o SQLAlchemy roda em Python puro).
- Se o `uv` falhar com `invalid peer certificate: UnknownIssuer`, algum antivírus ou proxy inspeciona o HTTPS: defina `UV_SYSTEM_CERTS=1`.

## Divisão da dupla
- Front-end e regras (Pessoa A): `web/`, `domain/`.
- Banco de dados (parceiro): `dados/`, migrações. Guia em `docs/banco-de-dados.md`.
