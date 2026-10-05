from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from circuitcrash.dados.carga import carregar_exemplo
from circuitcrash.dados.memoria import RepositorioMemoria
from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.dados.sql import RepositorioSQL

# Dia fixo para "hoje", "ontem" e as missões do dia não dependerem do relógio.
HOJE = date(2026, 10, 4)


def url_sqlite(pasta: Path) -> str:
    return f"sqlite:///{(pasta / 'teste.db').as_posix()}"


def criar_repo_sql(pasta: Path) -> RepositorioSQL:
    """SQLite em arquivo temporário, migrado e com os dados de exemplo."""
    url = url_sqlite(pasta)
    carregar_exemplo(url, hoje=HOJE)
    return RepositorioSQL(url, hoje=lambda: HOJE)


@pytest.fixture(params=["memoria", "sql"])
def repo(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[Repositorio]:
    if request.param == "memoria":
        yield RepositorioMemoria()
        return
    sql = criar_repo_sql(tmp_path)
    yield sql
    sql.fechar()
