# Plano — 012 Servidor MCP público do CircuitCrash

**Spec:** [spec.md](spec.md) · **Data:** 18/10/2026

## Resumo
`mcps/partida.py` ganha `Mesas`, que guarda uma `Mesa` por sessão MCP, e a `Mesa` passa a saber se grava ou não o resultado. As tools de `mcps/servidor.py` recebem o `Context` do SDK e pegam a mesa da sessão (`ctx.session`). `criar_servidor(repo, grava=...)` escolhe o modo e ajusta as instruções. `app.py` cria o servidor sem gravar sobre o mesmo repositório do site, acrescenta a rota de `streamable_http_app()` em `/mcp` e roda `session_manager.run()` no `lifespan` do Starlette. O `render.yaml` não muda: o MCP sobe com o site.

## Contexto técnico
| Item | Escolha |
| --- | --- |
| SDK | `mcp` 2.3: `MCPServer.streamable_http_app(streamable_http_path="/mcp", ...)` e `session_manager` |
| Transporte público | Streamable HTTP com sessão (`stateless_http=False`): a sessão MCP identifica a partida |
| Mesa por sessão | `weakref.WeakKeyDictionary[ServerSession, Mesa]`: quando o SDK descarta a sessão, a mesa vai junto |
| Limites | `session_idle_timeout=600` s, `max_sessions=100` |
| Segurança de transporte | `host="0.0.0.0"`, sem a proteção de DNS rebinding (é para servidor local) |
| Resultado sem gravar | `economia.resultado_da_demo` calcula; só o modo que grava chama `repo.registrar_partida`. Campo novo `gravado` em `ResultadoGravado` |
| Testes | `mcp.Client(servidor)` em processo para as mesas e o modo sem gravar; `httpx` + `TestClient` com `lifespan` para o `/mcp` do site |

## Checagem da constituição
- I Python: ok.
- II Spec antes de código: spec, plano e tarefas commitados antes.
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
    ├── partida.py          # + Mesa.grava, Mesas, campo gravado
    └── servidor.py         # tools com Context; criar_servidor(repo, grava=True); instruções por modo
tests/
├── test_mcp_partida.py     # + fim sem gravar
├── test_mcp_servidor.py    # + duas sessões, instruções do modo público
└── test_mcp_publico.py     # novo: /mcp do site por HTTP
README.md                   # + como conectar ao servidor público
```

## Riscos
- **Vários workers ou instâncias:** a mesa fica na memória de um processo. O Render gratuito roda uma instância com um processo (`uvicorn` sem `--workers`), então tudo bem. Se isso mudar, é preciso um armazenamento compartilhado ou o modo sem sessão.
- **`session_manager.run()` só pode rodar uma vez por servidor:** cada `criar_app` cria o seu servidor MCP, e os testes criam um app por teste.
