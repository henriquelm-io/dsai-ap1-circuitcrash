"""Consulta da loja pelo servidor MCP (spec 012)."""

import json

from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.domain import loja as regras
from circuitcrash.mcps import loja
from circuitcrash.mcps.loja import ItemCatalogo, RespostaLoja


def _item(resposta: RespostaLoja, avatar_id: str) -> ItemCatalogo:
    return next(item for item in resposta["catalogo"] if item["id"] == avatar_id)


def _compraveis(resposta: RespostaLoja) -> list[str]:
    return [item["id"] for item in resposta["catalogo"] if item["pode_comprar"]]


def test_saldo_suficiente(repo: Repositorio) -> None:
    resposta = loja.consultar_loja(repo, "lia.ohm")
    assert resposta["encontrado"]
    assert resposta["fagulhas"] == 900
    assert resposta["avatar_equipado"] == {"id": "resistor", "nome": "Resistor", "raridade": "Raro"}
    assert [a["id"] for a in resposta["possuidos"]] == ["onda", "resistor"]
    assert _compraveis(resposta) == ["faisca", "plug", "chip", "atomo"]
    assert resposta["compraveis"] == 4

    atomo = _item(resposta, "atomo")  # preço igual ao saldo
    assert atomo["preco"] == 900
    assert atomo["situacao"] == "comprar"
    assert atomo["faltam"] == 0
    nucleo = _item(resposta, "nucleo")
    assert nucleo["situacao"] == "falta"
    assert not nucleo["pode_comprar"]
    assert nucleo["faltam"] == 1100
    assert _item(resposta, "resistor")["situacao"] == "em_uso"
    assert _item(resposta, "resistor")["equipado"]
    onda = _item(resposta, "onda")
    assert onda["situacao"] == "possui"
    assert onda["possui"]
    assert not onda["pode_comprar"]
    assert "Átomo" in resposta["mensagem"]


def test_sem_saldo(repo: Repositorio) -> None:
    resposta = loja.consultar_loja(repo, "kai_k")
    assert resposta["fagulhas"] == 40
    assert _compraveis(resposta) == []
    assert resposta["compraveis"] == 0
    assert _item(resposta, "faisca")["faltam"] == 110
    assert all(item["faltam"] > 0 for item in resposta["catalogo"] if item["vendavel"])
    assert "Nenhum avatar cabe no saldo" in resposta["mensagem"]
    assert "150" in resposta["mensagem"]


def test_novato_sem_avatar(repo: Repositorio) -> None:
    resposta = loja.consultar_loja(repo, "luma_dev")
    assert resposta["encontrado"]
    assert resposta["fagulhas"] == 60
    assert resposta["avatar_equipado"] is None
    assert resposta["possuidos"] == []
    assert len(resposta["catalogo"]) == len(repo.listar_avatares()) == 8
    assert _item(resposta, "faisca")["faltam"] == 90  # o mesmo número de loja.comprar
    assert not any(item["possui"] or item["equipado"] for item in resposta["catalogo"])


def test_avatar_exclusivo_nao_e_vendavel(repo: Repositorio) -> None:
    lia = _item(loja.consultar_loja(repo, "lia.ohm"), "coroa")
    assert lia["raridade"] == "Exclusivo"
    assert lia["preco"] is None
    assert not lia["vendavel"]
    assert not lia["pode_comprar"]
    assert lia["situacao"] == "exclusivo"
    assert lia["faltam"] == 0

    nina = _item(loja.consultar_loja(repo, "ninacircuit"), "coroa")  # 1500 Fagulhas e já possui
    assert nina["possui"]
    assert nina["situacao"] == "possui"
    assert not nina["vendavel"]
    assert not nina["pode_comprar"]


def test_apelido_inexistente(repo: Repositorio) -> None:
    resposta = loja.consultar_loja(repo, "ninguem")
    assert not resposta["encontrado"]
    assert resposta["apelido"] == "ninguem"
    assert "Nenhum jogador" in resposta["mensagem"]
    assert resposta["catalogo"] == []
    assert resposta["possuidos"] == []
    assert resposta["avatar_equipado"] is None
    assert resposta["compraveis"] == 0


def test_apelido_sem_diferenciar_maiusculas(repo: Repositorio) -> None:
    resposta = loja.consultar_loja(repo, "  LIA.OHM ")
    assert resposta["encontrado"]
    assert resposta["apelido"] == "lia.ohm"


def test_consulta_nao_muda_nada(repo: Repositorio) -> None:
    antes = {j.id: (j.fagulhas, j.avatar_id, repo.inventario(j.id)) for j in repo.listar_jogadores()}
    for jogador in repo.listar_jogadores():
        loja.consultar_loja(repo, jogador.apelido)
    depois = {j.id: (j.fagulhas, j.avatar_id, repo.inventario(j.id)) for j in repo.listar_jogadores()}
    assert depois == antes


def test_respostas_nao_trazem_email(repo: Repositorio) -> None:
    respostas = [loja.consultar_loja(repo, j.apelido) for j in repo.listar_jogadores()]
    textos = json.dumps(respostas + [loja.consultar_loja(repo, "ninguem")], ensure_ascii=False)
    assert "@" not in textos


def test_situacao_igual_a_da_tela(repo: Repositorio) -> None:
    for jogador in repo.listar_jogadores():
        resposta = loja.consultar_loja(repo, jogador.apelido)
        meus = repo.inventario(jogador.id)
        esperado = [(a.id, regras.situacao(a, jogador, meus).value) for a in repo.listar_avatares()]
        assert [(item["id"], item["situacao"]) for item in resposta["catalogo"]] == esperado
