# Plano — 004 Publicação

**Spec:** [spec.md](spec.md) · **Data:** 05/10/2026

## Resumo
Um `render.yaml` na raiz descreve um Web Service no plano gratuito do Render, ligado à branch `main` com deploy automático. O build instala só as dependências de produção com `uv`. O início roda a carga de exemplo com `--recriar` e, só se ela der certo (`&&`), sobe o servidor pelo mesmo `python -m circuitcrash` de sempre, configurado por variáveis de ambiente. Nenhum código Python muda.

## Contexto técnico
| Item | Escolha |
| --- | --- |
| Hospedagem | Render, Web Service, `plan: free`, `runtime: python`, `branch: main`, `autoDeploy: true` |
| Python | `PYTHON_VERSION=3.14.2`, a mesma versão em que os testes rodam |
| Build | `pip install uv && uv sync --frozen --no-dev` (o `uv.lock` fixa as versões; o grupo `dev` não vai para o servidor) |
| Início | `.venv/bin/python -m circuitcrash.dados.carga --recriar && .venv/bin/python -m circuitcrash`. Usa o Python do `.venv` direto, para o `uv run` não sincronizar o grupo `dev` ao iniciar |
| Servidor | `HOST=0.0.0.0` e `RELOAD=0` no `render.yaml`; `PORT` vem do Render e o `__main__.py` já a lê |
| Banco | `DATABASE_URL=sqlite:///circuitcrash.db`, SQLite no disco do serviço, apagado a cada reinício (aceito pela spec) |
| Segredo | `SECRET_KEY` com `generateValue: true`: o Render gera o valor, que não aparece no repositório |
| Saúde | `healthCheckPath: /health` (rota já existente em `app.py`) |

## Checagem da constituição
- I Python: ok, nenhuma linguagem nova; o `render.yaml` é configuração.
- II Spec antes de código: ok, esta pasta.
- III Regras isoladas: `domain/` não muda.
- IV Contrato de dados: não muda.
- V Servidor decide: não muda.
- VI Celular: não muda nenhuma tela; o HTTPS vem do Render.
- VII Qualidade: os quatro checks continuam passando; nenhum segredo no repositório. O `.gitignore` passa a ignorar `.venv-*/`, para que ambientes paralelos (por exemplo `.venv-windows/`) não entrem por engano.

## Estrutura
```text
render.yaml   # novo: Web Service do Render
.gitignore    # + .venv-*/
README.md     # URL pública e passo a passo da publicação (depois do primeiro deploy)
```

## Validação local
Com `DATABASE_URL` apontando para um SQLite temporário, `SECRET_KEY=teste HOST=0.0.0.0 PORT=8123 RELOAD=0`, o comando de início carrega o exemplo, sobe o uvicorn em `0.0.0.0:8123` sem recarga, e `/health` responde `{"status":"ok"}`.

## Riscos
- Se o Render não oferecer o Python 3.14.2, o build falha logo no começo, com a mensagem no log: trocar `PYTHON_VERSION` por uma versão disponível a partir da 3.12 (o mínimo do `pyproject.toml`).
- O primeiro acesso depois de dormir demora alguns segundos (fora do escopo).
