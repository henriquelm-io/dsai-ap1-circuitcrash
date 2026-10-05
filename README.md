# CircuitCrash

Puzzle de circuitos por turnos para 4 jogadores, jogado no navegador do computador ou do celular. Ligue sua base à fonte de energia central, capture objetivos e troque Fagulhas por avatares.

**Dupla:** Henrique Lima e Severino Sobrinho

**Jogue online:** <https://circuitcrash.onrender.com/> (plano gratuito do Render: o primeiro acesso depois de um tempo parado pode levar alguns segundos)

Esta versão traz a **interface web completa**: partida de demonstração jogável, perfil, loja de avatares, ranking e regras. Os dados ficam num **banco SQLite** (ou PostgreSQL), ou em memória se nenhum banco for configurado. O login vem na próxima spec.

## Stack
| Camada | Tecnologia |
| --- | --- |
| Linguagem | Python 3.12+ (gerenciado com o `uv`) |
| Servidor web | Starlette, servido pelo Uvicorn |
| Telas | HTML gerado no servidor com Jinja2, CSS próprio e HTMX (o único JavaScript, carregado pronto) |
| Dados | SQLAlchemy 2 com migrações Alembic; SQLite por padrão, PostgreSQL opcional, ou dados em memória |
| Qualidade | pytest, ruff e mypy (modo estrito) |

## Como rodar (Windows)

1. Instale o **uv** no PowerShell (ele também instala o Python certo se precisar):
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   Feche e abra o terminal depois.
2. Na pasta do projeto, instale as dependências e crie o `.env`:
   ```powershell
   uv sync
   Copy-Item .env.example .env
   ```
3. Crie o banco e carregue os dados de exemplo (o `.env` já aponta para `sqlite:///circuitcrash.db`):
   ```powershell
   uv run python -m circuitcrash.dados.carga
   ```
4. Suba o servidor e abra <http://127.0.0.1:8000>:
   ```powershell
   uv run python -m circuitcrash
   ```

Se o `uv` der erro de certificado (`invalid peer certificate: UnknownIssuer`), algum antivírus ou proxy está inspecionando o HTTPS: rode `$env:UV_SYSTEM_CERTS = "1"` antes dos comandos.

### Banco de dados
| Para | Comando |
| --- | --- |
| Criar ou atualizar as tabelas | `uv run alembic upgrade head` |
| Carregar os dados de exemplo (só se o banco estiver vazio) | `uv run python -m circuitcrash.dados.carga` |
| Apagar tudo e recarregar o exemplo (antes de apresentar) | `uv run python -m circuitcrash.dados.carga --recriar` |
| Usar só dados em memória | deixe `DATABASE_URL=` vazio no `.env` |

Para usar **PostgreSQL**: `uv sync --extra postgres`, suba o banco (por exemplo, `docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=senha -e POSTGRES_DB=circuitcrash postgres:17`) e troque no `.env`: `DATABASE_URL=postgresql://postgres:senha@localhost:5432/circuitcrash`. Os mesmos comandos de carga funcionam.

No Linux ou macOS os comandos são os mesmos; o uv se instala com `curl -LsSf https://astral.sh/uv/install.sh | sh`.

### Testar no celular
Com o celular e o computador na mesma rede Wi-Fi:
```powershell
$env:HOST = "0.0.0.0"; uv run python -m circuitcrash
```
Descubra o IP do computador com `ipconfig` e abra `http://<ip>:8000` no celular. Se o Windows perguntar sobre o firewall, permita em redes privadas.

## Publicação (Render)
O serviço é descrito no `render.yaml` (spec `specs/004-publicacao/`). Um push na `main` publica a versão nova sozinho. A cada início, a carga roda com `--recriar` antes do servidor subir, então a demonstração sempre começa com os dados de exemplo; trocas de avatar somem quando o serviço reinicia ou dorme.

Para refazer a publicação do zero:
1. Entre em <https://dashboard.render.com> com a conta do GitHub e dê acesso ao repositório `dsai-ap1-circuitcrash`.
2. Clique em **New** → **Blueprint**, escolha o repositório e a branch `main`. O Render lê o `render.yaml` e mostra o Web Service `circuitcrash` (plano free).
3. Confirme em **Deploy Blueprint**. Não é preciso digitar nenhuma variável: a `SECRET_KEY` é gerada pelo Render e as outras estão no `render.yaml`.
4. Acompanhe o log do deploy até aparecer o servidor no ar (o build leva alguns minutos). Se o build falhar por causa do `PYTHON_VERSION`, troque no `render.yaml` por uma versão disponível a partir da 3.12.
5. Abra a URL que o Render mostra no topo da página do serviço e confira `/health`, que deve responder `{"status":"ok"}`. Depois navegue por início, partida, perfil, loja, ranking e regras, no computador e no celular.
6. Se a URL mudar, atualize o link **Jogue online** no começo deste README.

Para voltar ao estado inicial antes de apresentar, reinicie o serviço pelo painel do Render (**Restart service**) ou faça um novo deploy.

## Qualidade
```powershell
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy
```

## Como o projeto está organizado
| Pasta | O que tem |
| --- | --- |
| `src/circuitcrash/domain/` | Regras do jogo e da loja, em Python puro |
| `src/circuitcrash/dados/` | Contrato `Repositorio`, versão em memória (`memoria.py`) e com banco (`sql.py`, `tabelas.py`, `carga.py`) |
| `migracoes/` | Migrações do banco (Alembic) |
| `src/circuitcrash/web/` | Templates Jinja2, CSS e conversão do estado para a tela |
| `src/circuitcrash/app.py` | Rotas |
| `SPEC/` | Uma spec por funcionalidade, com data: o quê e por quê, critérios de aceitação e fora do escopo |
| `specs/` | Spec, plan e tasks de cada funcionalidade (Spec Kit) |
| `.specify/memory/constitution.md` | Regras do projeto |
| `docs/banco-de-dados.md` | Guia para ligar o banco de dados |
| `prompts/sessoes/` | Exportações das sessões com o agente de IA |

## Demonstração
- No cabeçalho, **Demo como** alterna entre `voltz_br` (veterano, com avatar) e `luma_dev` (usuário novo, sem avatar).
- Na partida, toque numa casa vazia ao lado do seu circuito para colocar a peça selecionada, ou numa peça do tabuleiro para girá-la. Dica: a curva da mão colocada à direita da sua peça em T liga você à fonte e captura a bateria.
- Com o banco, compras e trocas de avatar continuam depois de reiniciar o servidor. Para voltar ao estado inicial, rode a carga com `--recriar`. Sem banco (`DATABASE_URL` vazio), reiniciar volta tudo ao início.
- As missões do dia são carregadas para a data da carga: rode `--recriar` no dia da apresentação.

## Fluxo de trabalho
Cada funcionalidade nasce como `spec.md` → `plan.md` → `tasks.md` em `specs/NNN-nome/`, numa branch com o mesmo nome, e entra na `main` por Pull Request revisado pelo outro membro da dupla. A partir de 05/10, cada funcionalidade também tem uma spec datada em `SPEC/AAAA-MM-DD-nome.md`, commitada antes do código. Detalhes em `AGENTS.md`.

## Ferramentas e modelos de IA
| Ferramenta | Modelo | Para quê |
| --- | --- | --- |
| Claude Code (CLI da Anthropic) | Claude Opus 5.5 (`claude-opus-5-5`) | Specs, planos, tarefas, código, testes e documentação, sempre revisados pela dupla |
| Claude (app claude.ai, sessão de 01 a 05/10) | Claude Opus 5.5 | Telas de referência, cronograma, constituição e código inicial da spec 001 |

- O fluxo segue o **Spec Kit**: constituição em `.specify/memory/constitution.md` e `spec.md` → `plan.md` → `tasks.md` antes de qualquer código.
- As instruções para o agente ficam em `AGENTS.md` (o `CLAUDE.md` só aponta para ele), e a skill `/commit` (`.claude/skills/commit/SKILL.md`) roda os checks antes de cada commit.
- Todo commit diz quem ajudou e qual spec cumpre, nos trailers `Agent:` (ex.: `claude-code/claude-opus-5-5`) e `Spec:` (caminho da spec, ou `nenhuma`).
- As sessões exportadas do Claude Code estão em `prompts/sessoes/`.

## Contagem de linhas
Contado com o [cloc](https://github.com/AlDanial/cloc) 2.10 em 05/10/2026. Para refazer: `cloc src` e `cloc tests`.

### Código (`cloc src`)
```
-------------------------------------------------------------------------------
Language                     files          blank        comment           code
-------------------------------------------------------------------------------
Python                          13            332             88           1385
HTML                             9             21              0            503
CSS                              1             20             10            312
SVG                              1              0              0              1
-------------------------------------------------------------------------------
SUM:                            24            373             98           2201
-------------------------------------------------------------------------------
```

### Testes (`cloc tests`)
```
-------------------------------------------------------------------------------
Language                     files          blank        comment           code
-------------------------------------------------------------------------------
Python                           5            111              9            263
-------------------------------------------------------------------------------
SUM:                             5            111              9            263
-------------------------------------------------------------------------------
```
