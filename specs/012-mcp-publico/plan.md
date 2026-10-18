# Plano — 012 Servidor MCP público do CircuitCrash

**Spec:** [spec.md](spec.md) · **Data:** 18/10/2026 (refeito no mesmo dia, junto com a correção da spec: `partida_id` no lugar da sessão MCP)

## Resumo
`mcps/partida.py` ganha `Mesas`, que guarda cada `Mesa` por `partida_id`, com validade e limite, e a `Mesa` passa a saber o próprio id e se grava ou não o resultado. `criar_servidor(repo, publico=...)` escolhe o modo: o local grava e aceita `partida_id` vazio (a última partida iniciada); o público não grava e exige o id. As tools `ver_partida`, `jogar_peca` e `passar_vez` ganham `partida_id`, e as instruções e descrições mudam conforme o modo. `app.py` cria o servidor público sobre o mesmo repositório do site, acrescenta a rota de `streamable_http_app(stateless_http=True)` em `/mcp` e roda `session_manager.run()` no `lifespan` do Starlette. O `render.yaml` não muda: o MCP sobe com o site.

## Contexto técnico
| Item | Escolha |
| --- | --- |
| SDK | `mcp` 2.3, revisão 2026-07-28 do protocolo: cada pedido numa conexão nova, sem sessão |
| Transporte público | Streamable HTTP com `stateless_http=True` em `/mcp` |
| Estado da partida | `Mesas`: `dict[str, Mesa]` por `partida_id` (`secrets.token_urlsafe(9)`), com o último uso de cada uma |
| Limites | Validade de 30 min sem uso; no máximo 200 mesas (sai a de uso mais antigo). Relógio injetável (`time.monotonic` por padrão) para testar |
| Modo local | `partida_id` vazio resolve para a última partida iniciada; resultado gravado |
| Modo público | `partida_id` obrigatório; resultado calculado por `resultado_da_demo` e não gravado (`Mesa.grava=False`, campo `gravado` na resposta) |
| Segurança de transporte | `host="0.0.0.0"`, sem a proteção de DNS rebinding (é para servidor local) |
| Testes | `mcp.Client(servidor)` em processo para os dois modos; `TestClient` com `lifespan` e o transporte HTTP do cliente MCP sobre o app ASGI para o `/mcp` do site |

## Checagem da constituição
- I Python: ok.
- II Spec antes de código: spec corrigida, plano e tarefas commitados antes do código do servidor.
- III Regras isoladas: nenhuma regra nova; o cálculo continua em `domain/economia.py`.
- IV Contrato: `Repositorio` não muda.
- V Servidor decide: igual à 011.
- VI Celular: sem tela nova.
- VII Qualidade: testes, `ruff` e `mypy` estrito.

## Estrutura
```text
src/circuitcrash/
├── app.py                  # + rota /mcp e lifespan do MCP
└── mcps/
    ├── partida.py          # + Mesa.grava, Mesa.partida_id, Mesas, campos gravado e partida_id
    └── servidor.py         # criar_servidor(repo, publico=False); partida_id nas tools; instruções por modo
tests/
├── test_mcp_partida.py     # + fim sem gravar, Mesas (ids, validade, limite)
├── test_mcp_servidor.py    # + modo público: ids separados, id ausente ou desconhecido, não grava
└── test_mcp_publico.py     # novo: /mcp do site por HTTP
README.md                   # + como conectar ao servidor público
```

## Riscos
- **Vários workers ou instâncias:** as mesas ficam na memória de um processo. O Render gratuito roda uma instância com um processo (`uvicorn` sem `--workers`), então tudo bem. Se isso mudar, um `partida_id` pode cair noutro processo e virar "desconhecido".
- **Reinício do Render:** apaga as mesas; o agente recebe "partida não encontrada" e começa outra.
- **`session_manager.run()` só pode rodar uma vez por servidor:** cada `criar_app` cria o seu servidor MCP, e os testes criam um app por teste.
