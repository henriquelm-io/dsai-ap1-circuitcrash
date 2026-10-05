# Guia do banco de dados

O banco foi ligado na spec `002-banco-de-dados`. `RepositorioSQL` (`src/circuitcrash/dados/sql.py`) implementa o `Protocol` de `src/circuitcrash/dados/repositorio.py` com SQLAlchemy 2, e `criar_app()` o usa quando `DATABASE_URL` está preenchida; vazia, continua o `RepositorioMemoria`. Nenhum template e nenhuma regra em `domain/` mudou.

## Como está hoje
| Arquivo | O que faz |
| --- | --- |
| `dados/config.py` | `url_do_banco()` lê `DATABASE_URL`; `postgresql://` vira `postgresql+psycopg://` |
| `dados/tabelas.py` | Tabelas SQLAlchemy (lista abaixo, mais a coluna `ordem` em jogadores, avatares, missões e conquistas) |
| `dados/sql.py` | `RepositorioSQL`: cada método abre a própria sessão e devolve dataclasses novas |
| `dados/fabrica.py` | `criar_repositorio(url)`: memória ou banco |
| `dados/carga.py` | `python -m circuitcrash.dados.carga [--recriar]`: migra e carrega os dados de `memoria.py` |
| `migracoes/` + `alembic.ini` | Migrações Alembic; a URL vem do `.env` |

### Partidas gravadas (spec 006)
- `fagulhas_ganhas_hoje(jogador_id)`: soma de `participacoes.fagulhas` das partidas com `terminada_em` hoje. É o que o limite de 400 Fagulhas por dia usa.
- `registrar_partida(jogador_id, resultado)`: numa transação, insere `partidas` e `participacoes` e soma Fagulhas, rating, partidas, vitórias e objetivos ao jogador com `UPDATE ... SET x = x + :valor`. Se qualquer passo falhar, nada fica gravado.
- As contas de Fagulhas e rating ficam em `domain/economia.py`; o repositório só grava o resultado pronto.
- As partidas de exemplo terminam às 00:30 (menos alguns minutos), para uma partida jogada no dia da carga aparecer antes delas.

**Atenção:** como `RepositorioSQL` devolve objetos novos a cada chamada, mudar um `Jogador` não grava nada até chamar `salvar_jogador`.

### Criar uma migração nova
1. Atualize a branch com a `main` antes (para não criar duas migrações paralelas).
2. Mude `dados/tabelas.py`.
3. `uv run alembic revision --autogenerate --rev-id 0002 -m "descricao curta"` e revise o arquivo gerado em `migracoes/versions/`.
4. `uv run alembic upgrade head` e `uv run pytest` (os testes migram um SQLite temporário do zero).

## Passo a passo usado na spec 002
1. Abrir a spec `002-banco-de-dados` (spec → plan → tasks) antes de codar.
2. Adicionar as dependências: `uv add sqlalchemy alembic` (e `psycopg[binary]` se for PostgreSQL; SQLite não precisa de nada).
3. Criar `src/circuitcrash/dados/sql.py` com `class RepositorioSQL` implementando todos os métodos de `Repositorio`.
4. Criar as migrações com Alembic e um script de carga que insira os dados de exemplo de `dados/memoria.py`, para a demonstração continuar igual.
5. Em `criar_app()` (`src/circuitcrash/app.py`), usar `RepositorioSQL` quando a variável `DATABASE_URL` existir, senão `RepositorioMemoria`.
6. Rodar os mesmos testes contra as duas implementações: os testes de `tests/test_loja.py` devem passar com o banco também.

## Tabelas sugeridas
| Tabela | Colunas principais | Atende a |
| --- | --- | --- |
| `jogadores` | id, apelido (único), email (único), membro_desde, fagulhas, rating, partidas, vitorias, objetivos_capturados, avatar_id (FK, pode ser nulo) | `obter_jogador`, `listar_jogadores`, `salvar_jogador`, `ranking` |
| `avatares` | id, nome, raridade, descricao, cor, fundo, desenho | `listar_avatares`, `obter_avatar` |
| `inventario` | jogador_id (FK), avatar_id (FK), obtido_em; chave primária nas duas FKs | `inventario`, `adicionar_ao_inventario` |
| `partidas` | id, tipo (ranqueada/casual), iniciada_em, terminada_em | `partidas_recentes` |
| `participacoes` | partida_id, jogador_id, colocacao, pontos, variacao_rating, fagulhas | `partidas_recentes` |
| `missoes` e `progresso_missoes` | titulo, meta, recompensa / jogador_id, missao_id, dia, progresso | `missoes_do_dia` |
| `conquistas` e `progresso_conquistas` | nome, meta / jogador_id, conquista_id, progresso | `conquistas` |

Pensando no login com Google que vem depois: guarde em `jogadores` uma coluna `google_sub` (única, pode ser nula por enquanto), que é o identificador estável da conta Google. Nunca guarde senha.

## Regras que o banco deve respeitar
- `fagulhas` nunca fica negativo (use `CHECK (fagulhas >= 0)`).
- `avatar_id` do jogador precisa estar no inventário dele. O `domain/loja.py` já garante isso; o banco pode reforçar.
- A compra (`fagulhas -= preço` + inserir no inventário) deve acontecer numa única transação.
- `ranking()` devolve só jogadores com 5 partidas ou mais, ordenados por rating decrescente.
