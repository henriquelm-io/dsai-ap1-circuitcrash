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
