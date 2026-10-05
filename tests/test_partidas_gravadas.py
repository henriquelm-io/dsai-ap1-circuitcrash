"""Gravação das partidas terminadas (spec 006), contra a memória e o banco."""

from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.dados.sql import RepositorioSQL
from circuitcrash.dados.tabelas import TabelaParticipacao, TabelaPartida
from circuitcrash.domain import loja
from circuitcrash.domain.modelos import ResultadoPartida, ResumoPartida, TipoPartida
from conftest import HOJE, criar_repo_sql, url_sqlite


def resultado(
    colocacao: int = 1,
    pontos: int = 14,
    objetivos: int = 2,
    rating_antes: int = 1482,
    variacao: int = 9,
    fagulhas: int = 40,
    tipo: TipoPartida = TipoPartida.RANQUEADA,
) -> ResultadoPartida:
    return ResultadoPartida(tipo, colocacao, pontos, objetivos, rating_antes, variacao, fagulhas, False)


# ---------- Fagulhas do dia ----------


@pytest.mark.parametrize(("jogador_id", "fagulhas"), [("veterano", 75), ("novato", 35), ("nina", 0)])
def test_fagulhas_ganhas_hoje_no_exemplo(repo: Repositorio, jogador_id: str, fagulhas: int) -> None:
    assert repo.fagulhas_ganhas_hoje(jogador_id) == fagulhas


def test_jogador_inexistente_nao_ganhou_nada_hoje(repo: Repositorio) -> None:
    assert repo.fagulhas_ganhas_hoje("ninguem") == 0


def test_partida_gravada_soma_nas_fagulhas_do_dia(repo: Repositorio) -> None:
    repo.registrar_partida("veterano", resultado(fagulhas=40))
    repo.registrar_partida("veterano", resultado(colocacao=3, fagulhas=15, variacao=-3))
    assert repo.fagulhas_ganhas_hoje("veterano") == 75 + 40 + 15


def test_compra_nao_devolve_espaco_no_limite(repo: Repositorio) -> None:
    assert loja.comprar(repo, "veterano", "onda").ok
    assert repo.fagulhas_ganhas_hoje("veterano") == 75


# ---------- registrar a partida ----------


def test_registrar_atualiza_o_jogador(repo: Repositorio) -> None:
    repo.registrar_partida("veterano", resultado(colocacao=1, objetivos=2, variacao=9, fagulhas=40))
    veterano = repo.obter_jogador("veterano")
    assert veterano is not None
    assert veterano.fagulhas == 320 + 40
    assert veterano.rating == 1482 + 9
    assert veterano.partidas == 49
    assert veterano.vitorias == 15
    assert veterano.objetivos_capturados == 112 + 2


def test_derrota_nao_soma_vitoria(repo: Repositorio) -> None:
    repo.registrar_partida("veterano", resultado(colocacao=4, objetivos=0, variacao=-14, fagulhas=10))
    veterano = repo.obter_jogador("veterano")
    assert veterano is not None
    assert (veterano.vitorias, veterano.partidas, veterano.rating) == (14, 49, 1482 - 14)


def test_partida_gravada_vem_primeiro_nas_recentes(repo: Repositorio) -> None:
    antes = repo.partidas_recentes("veterano")
    repo.registrar_partida("veterano", resultado(colocacao=2, pontos=11, variacao=5, fagulhas=25))
    depois = repo.partidas_recentes("veterano")
    assert depois[0] == ResumoPartida(2, 11, 5, 25, "hoje")
    assert depois[1:] == antes[:4]


def test_partidas_gravadas_em_ordem_da_mais_nova(repo: Repositorio) -> None:
    repo.registrar_partida("nina", resultado(colocacao=3, pontos=5, variacao=-2, fagulhas=15))
    repo.registrar_partida("nina", resultado(colocacao=1, pontos=16, variacao=8, fagulhas=40))
    recentes = repo.partidas_recentes("nina")
    assert [p.colocacao for p in recentes] == [1, 3]


def test_partida_de_um_nao_aparece_para_outro(repo: Repositorio) -> None:
    repo.registrar_partida("nina", resultado())
    assert repo.partidas_recentes("kai") == []
    assert repo.fagulhas_ganhas_hoje("kai") == 0


def test_jogador_inexistente_nao_grava_nada(repo: Repositorio) -> None:
    with pytest.raises(ValueError):
        repo.registrar_partida("ninguem", resultado())
    assert repo.partidas_recentes("ninguem") == []
    assert repo.fagulhas_ganhas_hoje("ninguem") == 0


def test_novato_entra_no_ranking_na_quinta_partida(repo: Repositorio) -> None:
    assert "novato" not in [j.id for j in repo.ranking(100)]
    for _ in range(2):
        repo.registrar_partida("novato", resultado(rating_antes=1200, variacao=12, fagulhas=40))
    assert "novato" not in [j.id for j in repo.ranking(100)]
    repo.registrar_partida("novato", resultado(rating_antes=1224, variacao=12, fagulhas=40))
    novato = repo.obter_jogador("novato")
    assert novato is not None
    assert novato.partidas == 5
    assert not novato.provisorio
    assert novato.rating == 1236
    assert "novato" in [j.id for j in repo.ranking(100)]


def test_partida_com_zero_fagulhas(repo: Repositorio) -> None:
    repo.registrar_partida("veterano", resultado(fagulhas=0))
    veterano = repo.obter_jogador("veterano")
    assert veterano is not None and veterano.fagulhas == 320
    assert repo.partidas_recentes("veterano")[0].fagulhas == 0


# ---------- só com o banco ----------


def test_partida_continua_depois_de_reabrir_o_banco(tmp_path: Path) -> None:
    primeiro = criar_repo_sql(tmp_path)
    primeiro.registrar_partida("veterano", resultado(colocacao=1, variacao=9, fagulhas=40))
    primeiro.fechar()

    reaberto = RepositorioSQL(url_sqlite(tmp_path), hoje=lambda: HOJE)
    veterano = reaberto.obter_jogador("veterano")
    assert veterano is not None
    assert (veterano.fagulhas, veterano.rating, veterano.partidas) == (360, 1491, 49)
    assert reaberto.partidas_recentes("veterano")[0] == ResumoPartida(1, 14, 9, 40, "hoje")
    assert reaberto.fagulhas_ganhas_hoje("veterano") == 115
    reaberto.fechar()


def test_partida_grava_tipo_e_horario(tmp_path: Path) -> None:
    sql = criar_repo_sql(tmp_path)
    sql.registrar_partida("kai", resultado(tipo=TipoPartida.CASUAL, variacao=0, fagulhas=20))
    with Session(sql.motor) as sessao:
        partida = sessao.scalars(select(TabelaPartida).order_by(TabelaPartida.id.desc())).first()
        assert partida is not None
        assert partida.tipo == "casual"
        assert partida.terminada_em is not None and partida.terminada_em.date() == HOJE
    sql.fechar()


def test_jogador_inexistente_nao_deixa_partida_solta(tmp_path: Path) -> None:
    sql = criar_repo_sql(tmp_path)
    with Session(sql.motor) as sessao:
        partidas_antes = sessao.scalar(select(func.count()).select_from(TabelaPartida))
    with pytest.raises(ValueError):
        sql.registrar_partida("ninguem", resultado())
    with Session(sql.motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(TabelaPartida)) == partidas_antes
    sql.fechar()


def test_falha_no_meio_desfaz_tudo(tmp_path: Path) -> None:
    sql = criar_repo_sql(tmp_path)
    # Colocação 9 viola o CHECK da participação depois que a partida já foi inserida.
    with pytest.raises(Exception):  # noqa: B017 - o tipo depende do banco
        sql.registrar_partida("kai", resultado(colocacao=9))
    kai = sql.obter_jogador("kai")
    assert kai is not None and (kai.fagulhas, kai.partidas) == (40, 27)
    with Session(sql.motor) as sessao:
        participacoes = sessao.scalar(
            select(func.count()).select_from(TabelaParticipacao).where(TabelaParticipacao.jogador_id == "kai")
        )
        assert participacoes == 0
    sql.fechar()
