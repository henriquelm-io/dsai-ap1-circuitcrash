# Plano — 001 Interface web

**Spec:** [spec.md](spec.md) · **Data:** 04/10/2026

## Resumo
Aplicação Starlette que gera HTML com Jinja2. O tabuleiro é desenhado em SVG no servidor, e o HTMX troca só a área do jogo a cada jogada. Os dados vêm de `RepositorioMemoria`, que implementa o `Protocol` `Repositorio`.

## Contexto técnico
| Item | Escolha |
| --- | --- |
| Linguagem | Python 3.12+ |
| Servidor | Starlette + Uvicorn. O FastAPI é construído sobre o Starlette, então a migração depois não exige reescrever telas |
| Telas | Jinja2, CSS próprio, HTMX 2 via CDN |
| Sessão | `SessionMiddleware` com cookie assinado (`itsdangerous`) |
| Dados | `RepositorioMemoria` (dados de exemplo) |
| Testes | pytest + `starlette.testclient` |
| Qualidade | ruff (lint e formatação), mypy em modo strict |
| Alvo | Navegadores modernos de computador e celular |

## Checagem da constituição
- I Python: ok. O único JS é o HTMX.
- II Spec antes de código: ok, esta pasta.
- III Regras isoladas: `domain/tabuleiro.py` não importa nada de web nem de dados; o sorteio usa `random.Random(42)`.
- IV Contrato de dados: as rotas usam só `Repositorio`.
- V Servidor decide: os formulários mandam linha, coluna e índice; a validação fica em `domain/`.
- VI Celular: CSS com quebras em 1180, 900 e 560 px.
- VII Qualidade: testes em `tests/`.

## Estrutura
```text
src/circuitcrash/
├── app.py               # rotas e criação do app (criar_app)
├── __main__.py          # python -m circuitcrash
├── domain/
│   ├── tabuleiro.py     # regras da partida (puro)
│   ├── modelos.py       # Jogador, Avatar, Missao, Conquista...
│   └── loja.py          # comprar e equipar avatar
├── dados/
│   ├── repositorio.py   # Protocol: o contrato com o banco
│   └── memoria.py       # implementação com dados de exemplo
└── web/
    ├── visao.py         # estado -> dados prontos para o template
    ├── templates/       # base, inicio, partida, _jogo, perfil, loja, ranking, regras
    └── static/          # css, ícone
tests/                   # test_tabuleiro, test_loja, test_paginas
```

## Rotas
| Método | Caminho | O que faz |
| --- | --- | --- |
| GET | `/` | Início |
| GET | `/partida` | Tela da partida |
| POST | `/partida/selecionar` | Escolhe peça da mão (`indice`) |
| POST | `/partida/girar-mao` | Gira a peça selecionada |
| POST | `/partida/jogar` | Coloca ou gira na casa (`linha`, `coluna`) |
| POST | `/partida/passar` | Passa a vez |
| POST | `/partida/nova` | Recomeça a demonstração |
| GET | `/perfil` | Perfil do jogador da sessão |
| GET | `/loja?raridade=` | Loja com filtro |
| POST | `/loja/comprar` | Troca Fagulhas por avatar (`avatar_id`) |
| POST | `/loja/usar` | Usa um avatar do inventário |
| GET | `/ranking` | Ranking da temporada |
| GET | `/regras` | Regras |
| POST | `/jogador` | Troca o jogador da demonstração |
| GET | `/health` | Verificação de saúde |

As rotas `/partida/*` devolvem só o fragmento `_jogo.html` quando recebem o cabeçalho `HX-Request`; sem ele, redirecionam com 303 para `/partida`.

## Decisões
- **Estado da partida em memória, por sessão:** suficiente para a demonstração. O multiplayer vai trazer o estado para o servidor de partidas.
- **Tabuleiro como grade de botões com SVG dentro:** cada casa é um `<button>` acessível por teclado e leitor de tela.
- **Sem login:** a sessão guarda só qual jogador de exemplo está ativo.

## Pontos para a próxima spec (banco de dados)
Implementar `Repositorio` com SQLAlchemy em `dados/sql.py` e escolher a implementação em `criar_app()` pela variável `DATABASE_URL`. Detalhes em `docs/banco-de-dados.md`.
