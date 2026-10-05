from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.domain import loja

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
