from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from circuitcrash.dados.carga import carregar_exemplo
from circuitcrash.dados.config import normalizar_url, url_do_banco
from circuitcrash.dados.fabrica import criar_repositorio
from circuitcrash.dados.memoria import RepositorioMemoria
from circuitcrash.dados.sql import RepositorioSQL
from circuitcrash.dados.tabelas import TabelaInventario, TabelaJogador
from circuitcrash.domain import loja
from conftest import HOJE, criar_repo_sql, url_sqlite


@pytest.fixture
def sql(tmp_path: Path) -> Iterator[RepositorioSQL]:
    repo = criar_repo_sql(tmp_path)
    yield repo
    repo.fechar()


# ---------- paridade com os dados em memória ----------


def test_todos_os_metodos_devolvem_o_mesmo_que_a_memoria(sql: RepositorioSQL) -> None:
    memoria = RepositorioMemoria()
    assert sql.listar_jogadores() == memoria.listar_jogadores()
    assert sql.listar_avatares() == memoria.listar_avatares()
    assert sql.ranking() == memoria.ranking()
    assert sql.ranking(3) == memoria.ranking(3)
    for avatar in memoria.listar_avatares():
        assert sql.obter_avatar(avatar.id) == avatar
    for jogador in memoria.listar_jogadores():
        assert sql.obter_jogador(jogador.id) == jogador
        assert sql.inventario(jogador.id) == memoria.inventario(jogador.id)
        assert sql.partidas_recentes(jogador.id) == memoria.partidas_recentes(jogador.id)
        assert sql.partidas_recentes(jogador.id, 2) == memoria.partidas_recentes(jogador.id, 2)
        assert sql.missoes_do_dia(jogador.id) == memoria.missoes_do_dia(jogador.id)
        assert sql.conquistas(jogador.id) == memoria.conquistas(jogador.id)


def test_inexistentes_devolvem_none_ou_vazio(sql: RepositorioSQL) -> None:
    assert sql.obter_jogador("ninguem") is None
    assert sql.obter_avatar("nada") is None
    assert sql.inventario("ninguem") == set()
    assert sql.partidas_recentes("ninguem") == []


def test_os_dois_primeiros_jogadores_sao_os_da_demonstracao(sql: RepositorioSQL) -> None:
    assert [j.id for j in sql.listar_jogadores()[:2]] == ["veterano", "novato"]


# ---------- persistência ----------


def test_compra_sobrevive_a_reabrir_o_banco(tmp_path: Path) -> None:
    primeiro = criar_repo_sql(tmp_path)
    assert loja.comprar(primeiro, "veterano", "onda").ok
    assert loja.equipar(primeiro, "veterano", "onda").ok
    primeiro.fechar()

    reaberto = RepositorioSQL(url_sqlite(tmp_path), hoje=lambda: HOJE)
    veterano = reaberto.obter_jogador("veterano")
    assert veterano is not None
    assert veterano.fagulhas == 320 - 150
    assert veterano.avatar_id == "onda"
    assert "onda" in reaberto.inventario("veterano")
    reaberto.fechar()


def test_salvar_jogador_novo_entra_no_fim_da_lista(sql: RepositorioSQL) -> None:
    modelo = sql.obter_jogador("novato")
    assert modelo is not None
    novo = replace(modelo, id="zeca", apelido="zeca", email="zeca@exemplo.com")
    sql.salvar_jogador(novo)
    assert sql.obter_jogador("zeca") == novo
    assert sql.listar_jogadores()[-1].id == "zeca"


def test_adicionar_ao_inventario_duas_vezes_nao_duplica(sql: RepositorioSQL) -> None:
    sql.adicionar_ao_inventario("kai", "plug")
    sql.adicionar_ao_inventario("kai", "plug")
    assert sql.inventario("kai") == {"plug"}


# ---------- restrições do banco ----------


def test_fagulhas_negativas_sao_recusadas(sql: RepositorioSQL) -> None:
    kai = sql.obter_jogador("kai")
    assert kai is not None
    kai.fagulhas = -1
    with pytest.raises(IntegrityError):
        sql.salvar_jogador(kai)
    kai_no_banco = sql.obter_jogador("kai")
    assert kai_no_banco is not None and kai_no_banco.fagulhas == 40


def test_google_sub_repetido_e_recusado(sql: RepositorioSQL) -> None:
    with Session(sql.motor) as sessao:
        sessao.execute(update(TabelaJogador).where(TabelaJogador.id == "kai").values(google_sub="123"))
        sessao.commit()
        with pytest.raises(IntegrityError):
            sessao.execute(update(TabelaJogador).where(TabelaJogador.id == "lia").values(google_sub="123"))


def test_salvar_jogador_nao_apaga_google_sub(sql: RepositorioSQL) -> None:
    with Session(sql.motor) as sessao:
        sessao.execute(update(TabelaJogador).where(TabelaJogador.id == "kai").values(google_sub="123"))
        sessao.commit()
    kai = sql.obter_jogador("kai")
    assert kai is not None
    sql.salvar_jogador(kai)
    with Session(sql.motor) as sessao:
        assert sessao.scalar(select(TabelaJogador.google_sub).where(TabelaJogador.id == "kai")) == "123"


def test_inventario_exige_avatar_existente(sql: RepositorioSQL) -> None:
    with pytest.raises(IntegrityError):
        sql.adicionar_ao_inventario("kai", "nao-existe")


# ---------- carga de exemplo ----------


def _contar(sql: RepositorioSQL) -> tuple[int, int]:
    with Session(sql.motor) as sessao:
        jogadores = sessao.scalar(select(func.count()).select_from(TabelaJogador)) or 0
        itens = sessao.scalar(select(func.count()).select_from(TabelaInventario)) or 0
    return jogadores, itens


def test_carga_duas_vezes_nao_duplica(sql: RepositorioSQL, tmp_path: Path) -> None:
    antes = _contar(sql)
    assert carregar_exemplo(url_sqlite(tmp_path), hoje=HOJE) is False
    assert _contar(sql) == antes == (6, 8)


def test_recriar_volta_ao_estado_inicial(sql: RepositorioSQL, tmp_path: Path) -> None:
    assert loja.comprar(sql, "veterano", "onda").ok
    assert carregar_exemplo(url_sqlite(tmp_path), recriar=True, hoje=HOJE) is True
    veterano = sql.obter_jogador("veterano")
    assert veterano is not None and veterano.fagulhas == 320
    assert sql.inventario("veterano") == {"faisca", "plug"}


# ---------- escolha da implementação ----------


def test_criar_repositorio_escolhe_pela_url(tmp_path: Path) -> None:
    assert isinstance(criar_repositorio(None), RepositorioMemoria)
    assert isinstance(criar_repositorio(""), RepositorioMemoria)
    repo = criar_repositorio(url_sqlite(tmp_path))
    assert isinstance(repo, RepositorioSQL)
    repo.fechar()


def test_url_do_banco(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "   ")
    assert url_do_banco() is None
    monkeypatch.setenv("DATABASE_URL", "sqlite:///circuitcrash.db")
    assert url_do_banco() == "sqlite:///circuitcrash.db"
    monkeypatch.delenv("DATABASE_URL")
    assert url_do_banco() is None


def test_postgresql_usa_psycopg3() -> None:
    assert normalizar_url("postgresql://u:s@h/db") == "postgresql+psycopg://u:s@h/db"
    assert normalizar_url("postgres://u:s@h/db") == "postgresql+psycopg://u:s@h/db"
    assert normalizar_url("postgresql+psycopg://u:s@h/db") == "postgresql+psycopg://u:s@h/db"
