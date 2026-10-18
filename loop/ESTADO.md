# Estado do loop da contagem de linhas

Uma entrada por volta (spec 013). Quem escreve é o porteiro (a dupla), depois de rodar `loop/conferir.py` e `pytest`.

Como cada volta roda:

```bash
CLOC_PL=/caminho/cloc-2.10.pl claude -p --settings loop/permissoes.json --strict-mcp-config \
  --output-format stream-json --verbose < loop/PROMPT.md > volta-N.jsonl
```

`--settings` aplica as permissões da volta (o agente só edita o `README.md`), e `--strict-mcp-config` deixa o servidor MCP do projeto de fora (a volta não precisa dele). O rastro (`volta-N.jsonl`) fica fora do repositório. As sessões vão para `prompts/sessoes/` no fim do dia.

Modelo de entrada:

```markdown
## Volta N — DD/MM/AAAA HH:MM
- **Gatilho:** qual merge disparou.
- **O que o agente fez:** ferramentas chamadas e mudanças no README.
- **conferir.py:** saída e código (0, 1 ou 2).
- **pytest:** resultado.
- **Decisão do porteiro:** parar, tentar de novo ou escalar, e por quê.
```

## Volta 1 — 18/10/2026 19:07
- **Gatilho:** merge do PR #11 (spec 011, servidor MCP) na `main`, em 12/10. A contagem do README era de 05/10.
- **Sessão:** `claude -p` nova (`25e4ff31`), Claude Code 2.1.302, `claude-opus-5-5`; 11 turnos, cerca de 3 minutos, US$ 0,19.
- **O que o agente fez:** `conferir.py --cloc` junto com `date` (um comando só, permitido porque `date` está no `allow`) → `Grep` e `Read` da seção → quatro `Edit` no `README.md` (linha "Contado em", tabela, bloco de Código, bloco de Testes) → tentou `conferir.py; echo; pytest` num comando só, **negado** pelas permissões (`permission_denials`: o comando composto não casa com nenhuma regra) → rodou `conferir.py` e `pytest` separados. Nenhum arquivo além do `README.md` mudou.
- **Mudança:** código 2.965 → 3.460, testes 937 → 1.331, total 3.902 → 4.791 (entram a spec 011 e o próprio `loop/conferir.py` com os testes dele).
- **conferir.py (porteiro):** `PASSOU`, código 0.
- **pytest (porteiro):** 284 passaram.
- **Decisão do porteiro:** **parar.** O critério de parada passou na primeira volta, e o diff só mexe na seção da contagem. README e este arquivo commitados pelo porteiro.

## Volta 2 — 18/10/2026 19:23
- **Gatilho:** merge dos PRs #12 (spec 012, servidor MCP público) e #13 (este loop) na `main`, em 18/10. Antes da volta, o porteiro rodou `conferir.py` na `main`: `NÃO PASSOU` (código 3.460 no README contra 3.601 no `cloc`, testes 1.331 contra 1.523). A data já era de hoje, então só os números e os blocos estavam velhos.
- **Sessão:** `claude -p` nova (`8f7db964`), Claude Code 2.1.302, `claude-opus-5-5`; 12 turnos, cerca de 1,5 minuto, US$ 0,18. Rodada na branch `013-loop-volta-2`, criada da `main` (ninguém faz push direto na `main`).
- **O que o agente fez:** o mesmo caminho da volta 1. `cd` + `conferir.py --cloc` + `date` → `Grep` e `Read` da seção → cinco `Edit` no `README.md` (hora, tabela, e linhas dos dois blocos) → de novo tentou `conferir.py; echo; pytest` num comando só, **negado** outra vez → rodou os dois separados. Nenhum arquivo além do `README.md` mudou.
- **Mudança:** código 3.460 → 3.601, testes 1.331 → 1.523, total 4.791 → 5.124 (entra a spec 012).
- **conferir.py (porteiro):** `PASSOU`, código 0.
- **pytest (porteiro):** 300 passaram.
- **Decisão do porteiro:** **parar.** Passou na primeira volta deste evento.
