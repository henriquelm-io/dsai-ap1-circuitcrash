from circuitcrash.dados.memoria import RepositorioMemoria
from circuitcrash.domain import loja


def test_novato_nao_tem_avatar_e_nao_compra_sem_fagulhas() -> None:
    repo = RepositorioMemoria()
    novato = repo.obter_jogador("novato")
    assert novato is not None and novato.avatar_id is None
    resultado = loja.comprar(repo, "novato", "faisca")
    assert not resultado.ok
    assert "Faltam 90" in resultado.mensagem


def test_compra_desconta_e_equipa_primeiro_avatar() -> None:
    repo = RepositorioMemoria()
    novato = repo.obter_jogador("novato")
    assert novato is not None
    novato.fagulhas = 200
    assert loja.comprar(repo, "novato", "onda").ok
    assert novato.fagulhas == 50
    assert novato.avatar_id == "onda"
    assert "onda" in repo.inventario("novato")


def test_exclusivo_nao_e_vendido() -> None:
    repo = RepositorioMemoria()
    assert not loja.comprar(repo, "veterano", "coroa").ok


def test_nao_compra_duas_vezes() -> None:
    repo = RepositorioMemoria()
    assert not loja.comprar(repo, "veterano", "plug").ok


def test_equipar_so_o_que_possui() -> None:
    repo = RepositorioMemoria()
    assert loja.equipar(repo, "veterano", "plug").ok
    assert not loja.equipar(repo, "veterano", "nucleo").ok


def test_ranking_ignora_provisorios() -> None:
    repo = RepositorioMemoria()
    ids = [j.id for j in repo.ranking()]
    assert "novato" not in ids
    assert ids[0] == "nina"
