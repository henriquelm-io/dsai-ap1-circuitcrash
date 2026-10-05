# CircuitCrash

Puzzle de circuitos por turnos para 4 jogadores, jogado no navegador do computador ou do celular. Ligue sua base à fonte de energia central, capture objetivos e troque Fagulhas por avatares.

Esta versão traz a **interface web completa com dados de exemplo**: partida de demonstração jogável, perfil, loja de avatares, ranking e regras. Login e banco de dados vêm nas próximas specs.

## Como rodar (Windows)

1. Instale o **uv** no PowerShell (ele também instala o Python certo se precisar):
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   Feche e abra o terminal depois.
2. Na pasta do projeto:
   ```powershell
   uv sync
   uv run python -m circuitcrash
   ```
3. Abra <http://127.0.0.1:8000>.

No Linux ou macOS os comandos são os mesmos; o uv se instala com `curl -LsSf https://astral.sh/uv/install.sh | sh`.

### Testar no celular
Com o celular e o computador na mesma rede Wi-Fi:
```powershell
$env:HOST = "0.0.0.0"; uv run python -m circuitcrash
```
Descubra o IP do computador com `ipconfig` e abra `http://<ip>:8000` no celular. Se o Windows perguntar sobre o firewall, permita em redes privadas.

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
| `src/circuitcrash/dados/` | Contrato `Repositorio` e a versão em memória |
| `src/circuitcrash/web/` | Templates Jinja2, CSS e conversão do estado para a tela |
| `src/circuitcrash/app.py` | Rotas |
| `specs/` | Spec, plan e tasks de cada funcionalidade (Spec Kit) |
| `.specify/memory/constitution.md` | Regras do projeto |
| `docs/banco-de-dados.md` | Guia para ligar o banco de dados |

## Demonstração
- No cabeçalho, **Demo como** alterna entre `voltz_br` (veterano, com avatar) e `luma_dev` (usuário novo, sem avatar).
- Na partida, toque numa casa vazia ao lado do seu circuito para colocar a peça selecionada, ou numa peça do tabuleiro para girá-la. Dica: a curva da mão colocada à direita da sua peça em T liga você à fonte e captura a bateria.
- Os dados ficam em memória: reiniciar o servidor volta tudo ao estado inicial.

## Fluxo de trabalho
Cada funcionalidade nasce como `spec.md` → `plan.md` → `tasks.md` em `specs/NNN-nome/`, numa branch com o mesmo nome, e entra na `main` por Pull Request revisado pelo outro membro da dupla. Detalhes em `AGENTS.md`.
