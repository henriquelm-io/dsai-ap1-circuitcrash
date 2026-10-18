# Loop da contagem de linhas

**Data:** 18/10/2026 · **Status:** em implementação · **Branch:** `013-loop-contagem` · **Detalhes:** `specs/013-loop-contagem/`

## O quê
Um loop de agente para uma tarefa recorrente do CircuitCrash: **manter a seção "Contagem de linhas" do README igual ao `cloc`** com o comando do enunciado da AP1. O loop é desenhado em `loop/PROMPT.md` e rodado à mão: a dupla faz o papel do gatilho (abre uma sessão nova do agente) e do porteiro (roda a conferência e os testes e decide se para, tenta de novo ou escala). São no máximo três voltas.

## Por quê
É o exercício "um loop na aplicação da AP1". A contagem é uma tarefa real e repetida: o professor confere o número no README, e ele fica velho a cada merge (o do README é de 05/10, antes das specs 011 e 012).

## Gatilho: evento
**Merge na `main`.** A contagem só muda quando muda o código versionado, e todo código entra na `main` por merge de PR. Uma agenda (todo dia, toda semana) rodaria à toa quando nada entrou e deixaria o README errado entre um merge e a próxima execução. O deploy no Render já usa o mesmo evento (push na `main`).

## Critério de parada (conferível por máquina)
`uv run python loop/conferir.py` sai com código 0, e `uv run pytest` passa. O `conferir.py` roda o `cloc` e confere:
1. A tabela do README (código sem `tests/`, testes e total) tem os mesmos números do `cloc`.
2. Os blocos "### Código" e "### Testes" do README são iguais à saída do `cloc`.
3. A linha "Contado em" tem a data de hoje.
4. Só o `README.md` mudou em relação ao último commit.

## Quando o loop para e chama a dupla
- O `cloc` não roda ou não acha a seção "Contagem de linhas" no README.
- A contagem de código ou de testes caiu em relação à do README (código apagado precisa de olhar humano).
- Para passar, seria preciso mexer em qualquer arquivo que não seja o `README.md`.
- Os testes falham.
- Três voltas sem passar.

O agente só pode editar o `README.md`. Não pode tocar em `src/`, `tests/`, `migracoes/`, `specs/`, `SPEC/`, `prompts/`, `loop/` (inclusive o próprio `conferir.py` e o `ESTADO.md`), `diario/`, `.claude/`, `pyproject.toml`, `uv.lock`, `render.yaml` e `.mcp.json`, nem fazer commit ou push. Quem commita é o porteiro.

## Fora do escopo
- Rodar o loop sozinho (GitHub Actions ou agendador): fica como o que a dupla automatizaria primeiro, no diário.
- Mudar o comando do `cloc` do enunciado.
