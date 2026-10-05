---
name: commit
description: Faz um commit seguindo as regras do CircuitCrash — roda os quatro checks de qualidade, confere que nenhum segredo entra, escreve a mensagem em português no imperativo e pergunta antes do push. Use quando pedirem para commitar ou chamarem /commit.
---

# Commit do CircuitCrash

Siga os passos em ordem. Se qualquer passo falhar, pare e mostre o erro; não commite.

## 1. Qualidade (constituição, princípio VII)

Rode, um de cada vez, e pare no primeiro que falhar:

```
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy
```

Não corrija nada por conta própria nem pule um check: mostre a falha e pergunte como seguir.

## 2. O que vai entrar

1. Rode `git status` e mostre o resultado.
2. Prepare os arquivos com `git add` (todos, ou os que o pedido indicar).
3. Rode `git diff --cached --name-only` e confira a lista. Pare se aparecer:
   - `.env` ou qualquer `.env.*` que não seja `.env.example`;
   - qualquer coisa dentro de `.venv/`;
   - credenciais: `*.pem`, `*.key`, `*.p12`, `id_rsa*`, `credentials*`, `secrets*`, `*.db`, `*.sqlite3`.
4. Rode `git diff --cached` e procure segredos no conteúdo (chaves de API, tokens, senhas, `SECRET_KEY=` com valor real). `.env.example` só pode ter valores de exemplo.

Se achar algo, tire do stage (`git restore --staged <arquivo>`), avise e pergunte antes de continuar.

## 3. Mensagem

- Português, no imperativo, primeira linha com até 72 caracteres.
- Prefixo `feat:`, `fix:`, `docs:` ou `chore:`.
  - `feat`: funcionalidade nova; `fix`: correção; `docs`: só documentação ou specs; `chore`: configuração, dependências, ferramentas.
- Se a mudança é de uma spec, cite a pasta: pela branch (`NNN-nome`) ou pelos arquivos em `specs/NNN-nome/`. Ex.: `feat: adiciona loja de avatares (spec 001-loja)`.
- Corpo opcional, separado por uma linha em branco, explicando o porquê.

Exemplo:

```
feat: adiciona troca de avatar (spec 001-loja)

Valida no servidor se o jogador tem o avatar antes de equipar.
```

## 4. Commit

Faça o commit com a mensagem (use heredoc para várias linhas). Depois mostre `git log --oneline -1`.

## 5. Push

Pergunte antes de dar push, dizendo a branch e o remote (`git remote -v`). Lembre que a `main` só recebe mudanças por Pull Request revisado pela dupla; o push direto na `main` só vale se a pessoa confirmar.
