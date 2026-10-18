# Plano — 013 Loop da contagem de linhas

**Spec:** [spec.md](spec.md) · **Data:** 18/10/2026

## Resumo
A pasta `loop/` guarda o desenho e o rastro do loop: `PROMPT.md` (o que o agente lê em cada volta), `permissoes.json` (as permissões da volta, passadas com `--settings`), `conferir.py` (o porteiro conferível por máquina) e `ESTADO.md` (uma entrada por volta). Cada volta é um `claude -p` numa sessão nova, com o prompt na entrada. O agente roda o `cloc` e reescreve a seção "Contagem de linhas" do README. Depois, o porteiro (a dupla, nesta versão manual) roda `conferir.py` e `pytest`, anota em `ESTADO.md` e decide.

## Contexto técnico
| Item | Escolha |
| --- | --- |
| `cloc` | 2.10, script Perl fora do repositório; o caminho vai em `CLOC_PL` (o `cloc` não está instalado na máquina) |
| Comandos | Código: `perl $CLOC_PL . --vcs=git --exclude-dir=node_modules,vendor,dist,build,prompts,tests --exclude-lang=Markdown,JSON,YAML,CSV,Text,SVG --not-match-f='(lock\|\.min\.)'`. Testes: o mesmo filtro em `tests`, sem `tests` no `--exclude-dir`. Conferido: reproduz os 2.965 e 937 de 05/10 no commit `ff75be0` |
| Leitura do README | Seção do título `## Contagem de linhas` até o próximo `## `; números da tabela com ponto de milhar (`2.965`); blocos de código depois de `### Código` e `### Testes` |
| Arquivos mudados | `git status --porcelain` (rastreados e novos); só `README.md` é aceito |
| Queda | Tabela de `git show HEAD:README.md` contra o `cloc` de agora |
| Data | `Contado em DD/MM/AAAA` igual à data local de hoje |
| Permissões da volta | `allow`: `Read`, `Glob`, `Grep`, `Edit(./README.md)`, `Bash(perl:*)`, `Bash(git status:*)`, `Bash(git diff:*)`, `Bash(git log:*)`, `Bash(uv run python loop/conferir.py:*)`, `Bash(uv run pytest:*)`. `deny`: `Bash(git commit:*)`, `Bash(git push:*)`, `Edit` e `Write` em `loop/`, `src/`, `tests/` e o resto da lista da spec. No `-p`, o que não está em `allow` é negado sem perguntar |
| Nome do arquivo de permissões | `permissoes.json`: o `.gitignore` ignora `settings.json` |
| Testes | `tests/test_loop_conferir.py` importa `loop/conferir.py` pelo caminho (`importlib`) e testa as funções puras com READMEs de exemplo, sem rodar o `cloc` |

## Checagem da constituição
- I Python: ok.
- II Spec antes de código: spec, plano e tarefas commitados antes.
- III Regras isoladas: o loop não toca em `domain/`.
- IV Contrato: `Repositorio` não muda.
- V, VI: não se aplicam (sem tela, sem regra de jogo).
- VII Qualidade: testes do `conferir.py`, `ruff`; `mypy` estrito também no `conferir.py`.

## Estrutura
```text
loop/
├── PROMPT.md          # tarefa, gatilho, parada, limites; lido pelo agente em cada volta
├── permissoes.json    # --settings da volta
├── conferir.py        # porteiro: 0 passou, 1 tentar de novo, 2 escalar
└── ESTADO.md          # uma entrada por volta
diario/2026-10-13.md   # onde o loop parou e o que automatizar primeiro
tests/test_loop_conferir.py
README.md              # a seção "Contagem de linhas" é o que o agente muda
```

## Ordem das voltas
1. Commit do código do loop antes da primeira volta: o `cloc --vcs=git` só conta arquivos versionados, e o `conferir.py` também é código.
2. Volta: `claude -p --settings loop/permissoes.json < loop/PROMPT.md`, numa sessão nova, com `CLOC_PL` no ambiente.
3. Porteiro: `uv run python loop/conferir.py`, `uv run pytest`, entrada em `ESTADO.md`; se passou, commit do README e do `ESTADO.md`; se não passou, desfaz o README (`git checkout README.md`) ou deixa para a próxima volta, conforme a decisão anotada.
