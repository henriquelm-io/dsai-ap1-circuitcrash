"""Contas Google no repositório (spec 008), contra a memória e o banco."""

from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.domain.conta import ErroLogin, Identidade, entrar_com_google
from circuitcrash.domain.modelos import Jogador
from conftest import HOJE, criar_repo_sql

ANA = Identidade("1098765", "ana.souza@gmail.com", "Ana Souza")


def novo(jogador_id: str = "g-ana", apelido: str = "ana", email: str = "ana@gmail.com") -> Jogador:
    return Jogador(jogador_id, apelido, email, HOJE)


# ---------- métodos do contrato ----------


def test_criar_e_achar_pelo_sub_e_pelo_email(repo: Repositorio) -> None:
    repo.criar_jogador_google(novo(), "sub-ana")
    assert repo.obter_jogador_por_google("sub-ana") == novo()
    assert repo.obter_jogador_por_email("ana@gmail.com") == novo()
    assert repo.obter_jogador_por_email("ANA@Gmail.com") == novo()
    assert repo.obter_jogador("g-ana") == novo()


def test_jogador_criado_entra_no_fim_da_lista(repo: Repositorio) -> None:
    repo.criar_jogador_google(novo(), "sub-ana")
    assert repo.listar_jogadores()[-1].id == "g-ana"
    assert [j.id for j in repo.listar_jogadores()[:2]] == ["veterano", "novato"]


def test_inexistentes_devolvem_none(repo: Repositorio) -> None:
    assert repo.obter_jogador_por_google("nada") is None
    assert repo.obter_jogador_por_email("nada@exemplo.com") is None


def test_jogadores_do_exemplo_nao_tem_conta_google(repo: Repositorio) -> None:
    assert repo.obter_jogador_por_google("") is None
    assert repo.obter_jogador_por_email("voltz@exemplo.com") is not None


def test_vincular_google_uma_vez_so(repo: Repositorio) -> None:
    assert repo.vincular_google("kai", "sub-kai") is True
    assert repo.obter_jogador_por_google("sub-kai") is not None
    assert repo.vincular_google("kai", "sub-kai") is True  # a mesma conta de novo
    assert repo.vincular_google("kai", "sub-outro") is False
    kai = repo.obter_jogador_por_google("sub-kai")
    assert kai is not None and kai.id == "kai"


def test_vincular_jogador_inexistente(repo: Repositorio) -> None:
    assert repo.vincular_google("ninguem", "sub-x") is False


def test_salvar_jogador_mantem_a_conta_google(repo: Repositorio) -> None:
    repo.criar_jogador_google(novo(), "sub-ana")
    ana = repo.obter_jogador("g-ana")
    assert ana is not None
    ana.fagulhas = 40
    repo.salvar_jogador(ana)
    achada = repo.obter_jogador_por_google("sub-ana")
    assert achada is not None and achada.fagulhas == 40


# ---------- entrar com Google ----------


def test_primeira_entrada_cria_jogador(repo: Repositorio) -> None:
    jogador = entrar_com_google(repo, ANA, HOJE)
    assert jogador.apelido == "ana_souza"
    assert jogador.email == "ana.souza@gmail.com"
    assert (jogador.fagulhas, jogador.rating, jogador.partidas, jogador.avatar_id) == (0, 1200, 0, None)
    assert jogador.membro_desde == HOJE
    assert jogador.id.startswith("g-") and "1098765" not in jogador.id
    assert repo.obter_jogador(jogador.id) == jogador
    assert repo.inventario(jogador.id) == set()


def test_segunda_entrada_volta_ao_mesmo_jogador(repo: Repositorio) -> None:
    primeiro = entrar_com_google(repo, ANA, HOJE)
    primeiro.fagulhas = 55
    repo.salvar_jogador(primeiro)
    segundo = entrar_com_google(repo, ANA, date(2026, 10, 9))
    assert segundo.id == primeiro.id
    assert segundo.fagulhas == 55
    assert segundo.membro_desde == HOJE
    assert len(repo.listar_jogadores()) == 7


def test_mesmo_nome_ganha_outro_apelido(repo: Repositorio) -> None:
    entrar_com_google(repo, ANA, HOJE)
    outra = entrar_com_google(repo, Identidade("555", "ana2@gmail.com", "Ana Souza"), HOJE)
    assert outra.apelido == "ana_souza2"


def test_nome_igual_a_apelido_do_exemplo(repo: Repositorio) -> None:
    jogador = entrar_com_google(repo, Identidade("777", "v@gmail.com", "voltz_br"), HOJE)
    assert jogador.apelido == "voltz_br2"


def test_email_existente_e_ligado_sem_criar_outro(repo: Repositorio) -> None:
    jogador = entrar_com_google(repo, Identidade("888", "voltz@exemplo.com", "Outro Nome"), HOJE)
    assert jogador.id == "veterano"
    assert jogador.apelido == "voltz_br"
    assert len(repo.listar_jogadores()) == 6
    assert entrar_com_google(repo, Identidade("888", "voltz@exemplo.com", ""), HOJE).id == "veterano"


def test_email_ligado_a_outra_conta_e_recusado(repo: Repositorio) -> None:
    entrar_com_google(repo, Identidade("888", "voltz@exemplo.com", ""), HOJE)
    with pytest.raises(ErroLogin):
        entrar_com_google(repo, Identidade("999", "voltz@exemplo.com", ""), HOJE)


# ---------- só com o banco ----------


def test_sub_repetido_e_recusado_no_banco(tmp_path: Path) -> None:
    sql = criar_repo_sql(tmp_path)
    sql.criar_jogador_google(novo(), "sub-ana")
    with pytest.raises(IntegrityError):
        sql.criar_jogador_google(replace(novo(), id="g-outra", apelido="outra", email="o@gmail.com"), "sub-ana")
    assert sql.obter_jogador("g-outra") is None
    sql.fechar()
