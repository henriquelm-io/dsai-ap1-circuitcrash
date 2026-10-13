from datetime import date

from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.domain import loja
from circuitcrash.domain.modelos import Avatar, Jogador, Raridade

# Cada teste roda duas vezes: com RepositorioMemoria e com RepositorioSQL (fixture repo em conftest.py).


def test_novato_nao_tem_avatar_e_nao_compra_sem_fagulhas(repo: Repositorio) -> None:
    novato = repo.obter_jogador("novato")
    assert novato is not None and novato.avatar_id is None
    resultado = loja.comprar(repo, "novato", "faisca")
    assert not resultado.ok
    assert "Faltam 90" in resultado.mensagem


def test_compra_desconta_e_equipa_primeiro_avatar(repo: Repositorio) -> None:
    novato = repo.obter_jogador("novato")
    assert novato is not None
    novato.fagulhas = 200
    repo.salvar_jogador(novato)
    assert loja.comprar(repo, "novato", "onda").ok
    novato = repo.obter_jogador("novato")
    assert novato is not None
    assert novato.fagulhas == 50
    assert novato.avatar_id == "onda"
    assert "onda" in repo.inventario("novato")


def test_exclusivo_nao_e_vendido(repo: Repositorio) -> None:
    assert not loja.comprar(repo, "veterano", "coroa").ok


def test_nao_compra_duas_vezes(repo: Repositorio) -> None:
    assert not loja.comprar(repo, "veterano", "plug").ok


def test_equipar_so_o_que_possui(repo: Repositorio) -> None:
    assert loja.equipar(repo, "veterano", "plug").ok
    assert not loja.equipar(repo, "veterano", "nucleo").ok


def test_ranking_ignora_provisorios(repo: Repositorio) -> None:
    ids = [j.id for j in repo.ranking()]
    assert "novato" not in ids
    assert ids[0] == "nina"


# ---------- situação de cada avatar (spec 012) ----------


def _avatar(raridade: Raridade) -> Avatar:
    return Avatar("teste", "Teste", raridade, "", "#000", "#fff", "")


def _jogador(fagulhas: int, avatar_id: str | None = None) -> Jogador:
    return Jogador("j", "j", "j@exemplo.com", date(2026, 1, 1), fagulhas=fagulhas, avatar_id=avatar_id)


def test_situacao_em_uso_vem_antes_de_possui() -> None:
    assert loja.situacao(_avatar(Raridade.RARO), _jogador(0, "teste"), {"teste"}) is loja.Situacao.EM_USO


def test_situacao_possui() -> None:
    assert loja.situacao(_avatar(Raridade.RARO), _jogador(0), {"teste"}) is loja.Situacao.POSSUI


def test_situacao_exclusivo_mesmo_com_saldo_alto() -> None:
    assert loja.situacao(_avatar(Raridade.EXCLUSIVO), _jogador(100_000), set()) is loja.Situacao.EXCLUSIVO


def test_exclusivo_possuido_ou_em_uso() -> None:
    coroa = _avatar(Raridade.EXCLUSIVO)
    assert loja.situacao(coroa, _jogador(0), {"teste"}) is loja.Situacao.POSSUI
    assert loja.situacao(coroa, _jogador(0, "teste"), {"teste"}) is loja.Situacao.EM_USO


def test_situacao_comprar_inclusive_com_preco_igual_ao_saldo() -> None:
    assert loja.situacao(_avatar(Raridade.EPICO), _jogador(900), set()) is loja.Situacao.COMPRAR
    assert loja.situacao(_avatar(Raridade.COMUM), _jogador(1000), set()) is loja.Situacao.COMPRAR


def test_situacao_falta() -> None:
    assert loja.situacao(_avatar(Raridade.EPICO), _jogador(899), set()) is loja.Situacao.FALTA


def test_faltam() -> None:
    assert loja.faltam(_avatar(Raridade.COMUM), _jogador(60)) == 90
    assert loja.faltam(_avatar(Raridade.COMUM), _jogador(150)) == 0
    assert loja.faltam(_avatar(Raridade.COMUM), _jogador(500)) == 0
    assert loja.faltam(_avatar(Raridade.EXCLUSIVO), _jogador(0)) == 0


def test_valores_iguais_aos_do_template() -> None:
    assert [s.value for s in loja.Situacao] == ["em_uso", "possui", "exclusivo", "comprar", "falta"]
