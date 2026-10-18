# Spec 013 — Loop da contagem de linhas

**Branch:** `013-loop-contagem` · **Status:** em implementação · **Criada em:** 18/10/2026 · **Dono:** Severino · **Origem:** [SPEC/2026-10-18-loop-contagem.md](../../SPEC/2026-10-18-loop-contagem.md)

## Contexto
Exercício da disciplina (slide "Exercício: um loop na aplicação da AP1"): projetar um loop para a aplicação e rodar uma versão manual dele, com a dupla no papel do gatilho e do porteiro. O enunciado pede:

1. Uma tarefa recorrente da aplicação e o gatilho dela (agenda ou evento), com justificativa.
2. Um critério de parada que uma máquina consiga conferir ("ficar bom" não vale).
3. Quando o loop deve parar e chamar a dupla, incluindo as partes do código que ele não pode tocar.
4. Tudo em `loop/PROMPT.md`; rodar o agente com ele até três vezes, cada volta numa sessão nova. Depois de cada volta, a dupla é o porteiro: roda os testes e decide se para, tenta de novo ou escala.
5. Cada volta anotada em `loop/ESTADO.md` (o que o agente fez, se passou e por quê); em `diario/2026-10-13.md`, onde o loop parou e o que a dupla automatizaria primeiro. Commit no dia.

A dupla escolheu (18/10) a **contagem de linhas do README**: o professor confere esse número, e ele fica velho a cada merge. O do README é de 05/10, antes do merge da spec 011.

## Histórias de usuário

### H1 — Loop desenhado (prioridade P1)
Como dupla, queremos o loop descrito num arquivo que o agente leia sozinho, com tarefa, gatilho, critério de parada e limites.

Critérios de aceitação:
1. `loop/PROMPT.md` diz a tarefa, o gatilho (merge na `main`, evento) e a justificativa, o critério de parada, quando parar e chamar a dupla, e o que o agente não pode tocar.
2. O prompt basta para uma sessão nova, sem contexto da conversa: diz onde está o `cloc`, quais comandos rodar e como se conferir antes de terminar.
3. As permissões da volta (`loop/permissoes.json`) só deixam o agente editar o `README.md` e rodar os comandos de leitura e conferência; commit, push e edição de outros arquivos ficam negados.

### H2 — Porteiro conferível por máquina (P1)
Como porteiro, quero um comando que diga "passou" ou "não passou" e por quê, sem eu precisar julgar o README a olho.

Critérios de aceitação:
1. **Dado** o README atualizado com a saída do `cloc` de hoje e só ele mudado, **quando** rodo `uv run python loop/conferir.py`, **então** ele sai com 0 e diz que passou.
2. **Dado** um número da tabela diferente do `cloc`, um bloco "### Código" ou "### Testes" diferente da saída do `cloc`, ou a data de "Contado em" diferente de hoje, **então** ele sai com 1 e lista cada diferença.
3. **Dado** qualquer arquivo além do `README.md` mudado ou novo em relação ao último commit, **então** ele sai com 1 e nomeia os arquivos.
4. **Dado** uma contagem de código ou de testes menor que a do README antes da volta, ou o `cloc` sem rodar, ou a seção ausente, **então** ele sai com 2 (escalar), com o motivo.
5. A conta usa o comando do enunciado, igual ao de 05/10: código com `tests` a mais em `--exclude-dir`, e testes com o mesmo filtro só na pasta `tests`.

### H3 — Voltas registradas (P1)
Como dupla, queremos o rastro de cada volta e a conclusão.

Critérios de aceitação:
1. Até três voltas, cada uma com `claude -p` numa sessão nova, lendo `loop/PROMPT.md`.
2. `loop/ESTADO.md` tem, para cada volta: o que o agente fez, o resultado do `conferir.py` e do `pytest`, e a decisão do porteiro (parar, tentar de novo ou escalar) com o motivo.
3. `diario/2026-10-13.md` registra onde o loop parou, o que deu errado e o que a dupla automatizaria primeiro.

## Requisitos funcionais
- **RF-01** `loop/conferir.py` roda o `cloc` 2.10 com `perl` a partir do caminho em `CLOC_PL`. Sem a variável, sai com 2 e explica.
- **RF-02** Saída do `conferir.py`: 0 = passou; 1 = não passou, tentar de novo; 2 = escalar para a dupla. Cada problema numa linha.
- **RF-03** A contagem "antes da volta", usada para notar queda, é a tabela do README no último commit (`git show HEAD:README.md`).
- **RF-04** O `conferir.py` não muda nenhum arquivo.
- **RF-05** Nada em `src/` muda: o loop não mexe na aplicação.

## Critérios de sucesso
- **CS-01** O loop termina com o README igual ao `cloc` e o `conferir.py` saindo com 0, em até três voltas, ou para com o motivo registrado.
- **CS-02** Testes do `conferir.py` com READMEs de exemplo: passou, número errado, bloco errado, data velha, arquivo extra mudado e queda na contagem.
- **CS-03** `pytest`, `ruff` e `mypy` passam.

## Fora do escopo
- Rodar o loop sozinho por GitHub Actions ou agendador (vai para o diário como o que automatizar primeiro).
- Mudar o comando do `cloc` do enunciado.
- Atualizar outras partes do README.
