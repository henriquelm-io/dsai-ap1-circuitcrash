# Guia para ligar o banco de dados

As telas já funcionam com `RepositorioMemoria`. Para usar um banco de verdade, basta criar outra classe com os mesmos métodos do `Protocol` em `src/circuitcrash/dados/repositorio.py` e passá-la para `criar_app()`. Nenhum template e nenhuma regra em `domain/` precisa mudar.

## Passo a passo sugerido
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
