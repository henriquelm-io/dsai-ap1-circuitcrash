# Loop: contagem de linhas do README (spec 013)

Você é uma volta de um loop. Esta é uma sessão nova: não há conversa anterior. Tudo o que você precisa está aqui.

## Tarefa
Deixar a seção `## Contagem de linhas` do `README.md` igual ao `cloc` de agora, com o comando do enunciado da AP1. A contagem só muda quando o código muda, e o professor confere esse número.

## Gatilho
**Evento: merge na `main`.** Todo código entra na `main` por merge de PR, e a contagem só muda quando muda o código versionado. Uma agenda rodaria à toa quando nada entrou e deixaria o README errado entre um merge e a próxima execução. Nesta versão manual, a dupla faz o papel do gatilho e abre esta sessão depois do merge.

## O que fazer
1. Rode `uv run python loop/conferir.py --cloc`. Ele roda o `cloc` do enunciado e mostra as somas e as duas tabelas, prontas para copiar. (O `cloc` não está instalado; o caminho dele já está na variável `CLOC_PL`. Não rode o `perl` direto.)
2. Leia a seção `## Contagem de linhas` do `README.md` e atualize só ela:
   - a linha "Contado em DD/MM/AAAA, às HH:MM": a data de hoje e o horário em que você rodou o passo 1;
   - a tabela: "Código (sem `tests/`)", "Testes (`tests/`)" e "**Total**", com ponto de milhar (`3.460`);
   - o bloco de código depois de `### Código` e o depois de `### Testes`: cole a tabela do `cloc` exatamente como o passo 1 mostrou, da primeira à última linha de traços.
   Mantenha o resto da seção (o comando do `cloc` e as explicações) como está.
3. Confira você mesmo: `uv run python loop/conferir.py`. Se disser `NÃO PASSOU`, corrija o que ele listou e confira de novo.
4. Termine com um resumo curto: o que mudou no README e a última saída do `conferir.py`.

## Critério de parada (conferido por máquina)
A volta passou quando `uv run python loop/conferir.py` sai com `PASSOU` (código 0) e `uv run pytest -q` passa. O `conferir.py` confere: tabela igual ao `cloc`, os dois blocos iguais às tabelas do `cloc`, "Contado em" com a data de hoje e nenhum arquivo além do `README.md` mudado.

## Quando parar e chamar a dupla
Pare sem insistir, e diga o motivo no resumo, se:
- o `conferir.py` disser `ESCALAR` (seção ausente, `cloc` sem rodar ou contagem menor que a do README: pode ser código apagado);
- para passar, fosse preciso mexer em qualquer arquivo que não seja o `README.md`;
- os testes falharem;
- você não conseguir passar depois de duas tentativas de correção nesta volta.

## O que você não pode tocar
Você só pode editar o `README.md`, e dentro dele só a seção `## Contagem de linhas`. Não mexa em `src/`, `tests/`, `migracoes/`, `specs/`, `SPEC/`, `prompts/`, `diario/`, `loop/` (nem neste arquivo, nem no `conferir.py`, nem no `ESTADO.md`), `.claude/`, `pyproject.toml`, `uv.lock`, `render.yaml` ou `.mcp.json`. Não faça commit, push, checkout nem reset: quem decide e commita é o porteiro (a dupla).
