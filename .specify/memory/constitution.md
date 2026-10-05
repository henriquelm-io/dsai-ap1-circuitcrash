# Constituição do CircuitCrash

Versão 1.0.0 · Ratificada em 04/10/2026

O CircuitCrash é um jogo web de puzzle por turnos para 4 jogadores. Esta constituição vale para todas as specs, planos e tarefas do projeto, para as pessoas e para os agentes de IA.

## Princípios

### I. Python em todo o projeto
O servidor, as regras do jogo e o acesso a dados são escritos em Python 3.12 ou superior, com dependências gerenciadas pelo `uv`. As telas são HTML gerado no servidor com Jinja2; o único JavaScript permitido é a biblioteca HTMX, usada pronta.

### II. Spec antes de código (inegociável)
Nenhuma funcionalidade é implementada sem `spec.md`, `plan.md` e `tasks.md` na pasta `specs/NNN-nome/`. A spec descreve o quê e por quê, sem tecnologia. O plano descreve como. As tarefas são pequenas, em ordem e testáveis.

### III. Regras do jogo isoladas
O pacote `circuitcrash.domain` não acessa banco, rede nem relógio, e todo sorteio usa semente. O mesmo estado com a mesma ação produz sempre o mesmo resultado.

### IV. Dados atrás de um contrato
As telas e as regras só falam com o `Protocol` `circuitcrash.dados.repositorio.Repositorio`. Trocar o repositório em memória pelo banco não pode exigir mudança em templates nem em `domain/`.

### V. O servidor decide
O navegador só envia intenções (por exemplo, "jogar na linha 2, coluna 3"). Toda jogada, compra e troca de avatar é validada no servidor.

### VI. Funciona no celular
Toda tela funciona a partir de 360 px de largura sem rolagem horizontal, com alvos de toque de pelo menos 44 px. As telas funcionam mesmo se o HTMX não carregar.

### VII. Qualidade antes do commit
Todo comportamento novo tem teste em `pytest`. `ruff check`, `ruff format --check` e `mypy` passam sem erros antes de qualquer commit. Segredos ficam só no `.env`, que nunca é versionado.

## Fluxo de trabalho
- Uma branch por spec, com o nome da pasta (`002-banco-de-dados`).
- Entra na `main` só por Pull Request revisado pelo outro membro da dupla.
- Mudanças em `dados/repositorio.py` ou nesta constituição precisam do aceite dos dois.

## Governança
Esta constituição prevalece sobre qualquer outra orientação. Emendas são feitas por PR que atualize a versão e a data acima.
