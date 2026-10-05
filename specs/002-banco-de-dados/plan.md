# Plano — 002 Banco de dados

**Spec:** [spec.md](spec.md) · **Data:** 04/10/2026

## Resumo
Nova classe `RepositorioSQL` em `dados/sql.py`, que implementa o `Protocol` `Repositorio` com SQLAlchemy 2. As tabelas seguem `docs/banco-de-dados.md` e são criadas por migrações Alembic. `criar_app()` escolhe a implementação pela variável `DATABASE_URL`: vazia, `RepositorioMemoria`; preenchida, `RepositorioSQL`. O padrão sugerido é SQLite em arquivo (`sqlite:///circuitcrash.db`), e o PostgreSQL só entra quando a URL apontar para ele. Um script de carga copia os dados de exemplo de `dados/memoria.py` para o banco.

## Contexto técnico
| Item | Escolha |
| --- | --- |
| ORM | SQLAlchemy 2 (`Mapped`, `mapped_column`), modo síncrono, tipado para o mypy strict |
| Migrações | Alembic, com a pasta `migracoes/` na raiz e `alembic.ini` |
| Banco padrão | SQLite em arquivo; não precisa instalar nada |
| Banco opcional | PostgreSQL com `psycopg[binary]`, no extra `postgres` (`uv sync --extra postgres`) |
| Configuração | `DATABASE_URL` no `.env`, lido com `python-dotenv` só nos pontos de entrada (servidor, carga, Alembic), nunca ao importar o app |
| Testes | pytest com fixture parametrizada: `memoria` e `sql` (SQLite em arquivo temporário, migrado e carregado) |

## Checagem da constituição
- I Python: ok. SQLAlchemy, Alembic e psycopg são Python.
- II Spec antes de código: ok, esta pasta.
- III Regras isoladas: `domain/` não muda e não importa nada de `dados/sql.py`.
- IV Contrato de dados: `RepositorioSQL` implementa o `Repositorio` sem mudar a assinatura. Os objetos do SQLAlchemy não saem de `dados/`: os métodos devolvem as dataclasses de `domain/modelos.py`.
- V Servidor decide: sem mudança.
- VI Celular: sem mudança de tela.
- VII Qualidade: testes rodam contra as duas implementações; `ruff` e `mypy` cobrem o código novo. O `.env` e o `*.db` já estão no `.gitignore`.

## Estrutura
```text
alembic.ini                      # aponta para migracoes/
migracoes/
├── env.py                       # usa a URL de dados/config.py e o metadata de dados/tabelas.py
├── script.py.mako
└── versions/
    └── 0001_tabelas_iniciais.py # todas as tabelas desta spec
src/circuitcrash/
├── app.py                       # criar_app() usa criar_repositorio() quando repo não é passado
├── __main__.py                  # passa env_file=".env" ao uvicorn quando o arquivo existe
└── dados/
    ├── config.py                # url_do_banco(): lê DATABASE_URL e normaliza postgresql:// -> postgresql+psycopg://
    ├── fabrica.py               # criar_repositorio(url): RepositorioMemoria ou RepositorioSQL
    ├── tabelas.py               # modelos SQLAlchemy (Base e tabelas)
    ├── sql.py                   # RepositorioSQL
    └── carga.py                 # python -m circuitcrash.dados.carga [--recriar]
tests/
├── conftest.py                  # fixture repo parametrizada (memoria, sql)
├── test_loja.py                 # passa a usar a fixture repo
├── test_banco.py                # paridade memória x banco, persistência, restrições
└── test_paginas.py              # + telas abrindo com RepositorioSQL
```

## Tabelas
Todas as tabelas de `docs/banco-de-dados.md`, com estes acréscimos:

| Tabela | Colunas | Observações |
| --- | --- | --- |
| `jogadores` | id (texto, PK), ordem, apelido, email, google_sub, membro_desde, fagulhas, rating, partidas, vitorias, objetivos_capturados, avatar_id | `apelido`, `email` e `google_sub` únicos; `google_sub` pode ser nulo; `CHECK (fagulhas >= 0)`; `avatar_id` FK para `avatares`, pode ser nulo |
| `avatares` | id (texto, PK), ordem, nome, raridade, descricao, cor, fundo, desenho | `raridade` guarda o valor do `Raridade` (`comum`…`exclusivo`) com `CHECK` |
| `inventario` | jogador_id, avatar_id, obtido_em | PK nas duas FKs |
| `partidas` | id (inteiro, PK), tipo, iniciada_em, terminada_em | `tipo` em `ranqueada`/`casual` |
| `participacoes` | partida_id, jogador_id, colocacao, pontos, variacao_rating, fagulhas | PK em partida_id + jogador_id; `colocacao` entre 1 e 4 |
| `missoes` | id, ordem, titulo, meta, recompensa | |
| `progresso_missoes` | jogador_id, missao_id, dia, progresso | PK nas três primeiras |
| `conquistas` | id, ordem, nome, meta | |
| `progresso_conquistas` | jogador_id, conquista_id, progresso | PK nas duas primeiras |

A coluna `ordem` garante a mesma ordem da spec 001: `listar_jogadores()[:2]` continua devolvendo os perfis da demonstração, e a loja lista do Comum ao Exclusivo. No SQLite, as chaves estrangeiras são ligadas com `PRAGMA foreign_keys=ON` em cada conexão.

## Como cada método responde
| Método | Consulta |
| --- | --- |
| `obter_jogador`, `listar_jogadores` | `jogadores` por id / por `ordem` |
| `salvar_jogador` | atualiza se o id existe, insere com a próxima `ordem` se não; não mexe em `google_sub` |
| `ranking(limite)` | `partidas >= 5`, por `rating` decrescente e `ordem` crescente no empate |
| `listar_avatares`, `obter_avatar` | `avatares` por `ordem` / por id |
| `inventario`, `adicionar_ao_inventario` | `inventario`; adicionar ignora se já existe |
| `partidas_recentes(limite)` | `participacoes` + `partidas`, da mais recente para a mais antiga; `quando` vira "hoje", "ontem" ou "dd/mm" pela data de término |
| `missoes_do_dia` | todas as `missoes` por `ordem`, com o progresso de hoje (0 se não houver) |
| `conquistas` | todas as `conquistas` por `ordem`, com o progresso do jogador (0 se não houver) |

Cada método abre a própria sessão com `with sessao.begin()` e devolve dataclasses novas. Por isso, quem altera um `Jogador` precisa chamar `salvar_jogador` para gravar: é o que `domain/loja.py` já faz.

## Escolha da implementação
```python
def criar_repositorio(url: str | None) -> Repositorio:
    if not url:
        return RepositorioMemoria()
    return RepositorioSQL(url)
```
`criar_app(repo=None)` usa `criar_repositorio(url_do_banco())`. Os testes continuam passando um repositório pronto. O `.env.example` passa a sugerir `DATABASE_URL=sqlite:///circuitcrash.db`, com um comentário mostrando a URL do PostgreSQL.

## Carga de exemplo
`uv run python -m circuitcrash.dados.carga`:
1. Roda `alembic upgrade head`.
2. Se `jogadores` já tem linhas, avisa e sai sem duplicar nada. Com `--recriar`, apaga os dados de todas as tabelas e carrega de novo.
3. Insere `AVATARES`, `JOGADORES` e `INVENTARIOS` de `dados/memoria.py`, na mesma ordem.
4. Cria uma partida para cada `ResumoPartida` de `PARTIDAS`, com a participação do jogador. "hoje" e "ontem" viram a data da carga e a véspera; "28/09" vira 28/09 do ano corrente.
5. Insere as três missões e o progresso de hoje igual ao da memória (1 de 2 em "Jogue 2 partidas").
6. Insere as seis conquistas e o progresso de cada jogador com a mesma conta que `RepositorioMemoria.conquistas` faz.

## Testes
- `tests/conftest.py`: fixture `repo` com `params=["memoria", "sql"]`. A versão `sql` cria um SQLite em `tmp_path`, roda as migrações e a carga, e devolve o `RepositorioSQL`.
- `tests/test_loja.py`: os seis testes passam a receber `repo` e rodam duas vezes. O teste de compra passa a salvar o novato depois de mudar as Fagulhas e a reler do repositório antes de conferir (ponto 2 da spec).
- `tests/test_banco.py`: todos os métodos do contrato devolvem o mesmo que a memória logo após a carga; uma compra sobrevive a um `RepositorioSQL` novo sobre o mesmo arquivo; gravar Fagulhas negativas falha; `google_sub` repetido falha; a carga rodada duas vezes não duplica; `criar_repositorio` escolhe certo pela URL.
- `tests/test_paginas.py`: as telas abrem com `criar_app(RepositorioSQL(...))`.
- O PostgreSQL não entra nos testes automáticos. Ele é conferido à mão, se houver tempo (tarefa opcional).

## Decisões
- **SQLite por padrão:** é só um arquivo, roda igual no Windows e no Linux e não exige Docker para a entrega de terça.
- **Contrato sem mudança:** a compra continua em duas chamadas (ponto 1 da spec). O banco reforça com `CHECK (fagulhas >= 0)`.
- **Sem reforço de "avatar em uso precisa estar no inventário" no banco:** a regra já está em `domain/loja.py`, e a trava no banco complicaria a carga. Fica para depois, se for preciso.
- **`.env` só nos pontos de entrada:** importar `circuitcrash.app` nos testes não lê o `.env`, então os testes não dependem da máquina de quem roda.
- **Migração escrita a partir do autogenerate e revisada à mão:** um arquivo só para as tabelas iniciais.

## Riscos
- **Smart App Control do Windows:** o SQLAlchemy traz extensões compiladas (e o `greenlet` como dependência). Se forem bloqueadas, como aconteceu com o `ast-serialize` (ver `AGENTS.md`), use `DISABLE_SQLALCHEMY_CEXT_RUNTIME=1` ou fixe uma versão anterior e registre no `AGENTS.md`.
- **Certificado TLS nesta máquina:** o `uv` precisou de `UV_SYSTEM_CERTS=1` para baixar pacotes. Isso vale para o `uv add` das dependências novas.
- **Compras simultâneas do mesmo jogador** podem sobrescrever as Fagulhas uma da outra. Não acontece na demonstração (um navegador por jogador). Resolve-se junto com o ponto 1.

## Pontos para as próximas specs
- Login Google: preencher `google_sub` e procurar o jogador por ele (método novo no contrato).
- Partida real e economia: gravar `partidas` e `participacoes` ao fim da partida, aplicar Fagulhas, o limite diário e o rating numa transação.
