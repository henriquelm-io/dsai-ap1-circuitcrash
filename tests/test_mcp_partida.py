"""Partida jogada pelo servidor MCP (spec 011)."""

import dataclasses

from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.domain import tabuleiro
from circuitcrash.mcps import partida
from circuitcrash.mcps.partida import Mesa


def _iniciada(repo: Repositorio, apelido: str = "luma_dev") -> Mesa:
    mesa = Mesa()
    resposta = partida.iniciar(repo, mesa, apelido)
    assert resposta["ativa"]
    return mesa


def _ate_o_fim(repo: Repositorio, mesa: Mesa) -> partida.RespostaPartida:
    resposta = partida.ver(mesa)
    while not resposta["terminou"]:
        resposta = partida.passar(repo, mesa)
    return resposta


def test_sem_partida_responde_sem_erro(repo: Repositorio) -> None:
    mesa = Mesa()
    for resposta in (partida.ver(mesa), partida.passar(repo, mesa), partida.jogar(repo, mesa, 0, 0, 2, 3)):
        assert not resposta["ativa"]
        assert not resposta["aceita"]
        assert "iniciar_partida" in resposta["mensagem"]


def test_iniciar_com_apelido_inexistente(repo: Repositorio) -> None:
    mesa = Mesa()
    resposta = partida.iniciar(repo, mesa, "ninguem")
    assert not resposta["ativa"]
    assert "ninguem" in resposta["mensagem"]
    assert mesa.estado is None


def test_iniciar_mostra_a_partida_de_demonstracao(repo: Repositorio) -> None:
    mesa = Mesa()
    resposta = partida.iniciar(repo, mesa, " LUMA_DEV ")
    assert resposta["apelido"] == "luma_dev"
    assert resposta["rodada"] == 6
    assert resposta["max_rodadas"] == tabuleiro.MAX_RODADAS
    assert resposta["rodadas_restantes"] == 7
    assert not resposta["terminou"]
    assert [(p["jogador"], p["pontos"]) for p in resposta["placar"]] == [
        ("Você", 4),
        ("Lia", 9),
        ("Bruno", 6),
        ("Kai", 3),
    ]
    assert len(resposta["mao"]) == tabuleiro.TAMANHO_MAO
    assert resposta["mao"][0] == {"indice": 0, "formato": "curva", "saidas": "SW"}
    assert {
        "linha": 3,
        "coluna": 3,
        "tipo": "fonte",
        "saidas": "",
        "dono": None,
        "objetivo": None,
        "capturado_por": None,
    } in (resposta["casas"])
    assert all(c["tipo"] != "vazia" for c in resposta["casas"])


def test_jogadas_validas_incluem_a_curva_que_liga_a_fonte(repo: Repositorio) -> None:
    resposta = partida.ver(_iniciada(repo))
    assert {"peca": 0, "giros": 0, "linha": 2, "coluna": 3, "saidas": "SW"} in resposta["jogadas_validas"]
    for jogada in resposta["jogadas_validas"]:
        estado = tabuleiro.nova_partida()
        tabuleiro.selecionar(estado, jogada["peca"])
        for _ in range(jogada["giros"]):
            tabuleiro.girar_selecionada(estado)
        assert tabuleiro.jogar_na_casa(estado, jogada["linha"], jogada["coluna"])


def test_jogada_valida_passa_a_vez_e_pontua(repo: Repositorio) -> None:
    mesa = _iniciada(repo)
    resposta = partida.jogar(repo, mesa, 0, 0, 2, 3)
    assert resposta["aceita"]
    assert resposta["rodada"] == 7
    assert resposta["placar"][0] == {"jogador": "Você", "pontos": 7, "energizado": True}
    assert "Bateria" in resposta["mensagem"]


def test_jogada_recusada_nao_gasta_a_vez_nem_gira_a_peca(repo: Repositorio) -> None:
    mesa = _iniciada(repo)
    resposta = partida.jogar(repo, mesa, 0, 1, 6, 3)
    assert not resposta["aceita"]
    assert resposta["rodada"] == 6
    assert "circuito" in resposta["mensagem"]
    assert resposta["mao"][0]["saidas"] == "SW"


def test_giros_sao_aplicados_antes_de_jogar(repo: Repositorio) -> None:
    mesa = _iniciada(repo)
    # Girada 2 vezes, a curva SW vira NE e não liga mais em (2,3).
    assert not partida.jogar(repo, mesa, 0, 2, 2, 3)["aceita"]
    # Girada 4 vezes, volta a SW.
    assert partida.jogar(repo, mesa, 0, 4, 2, 3)["aceita"]


def test_peca_fora_da_mao_e_recusada(repo: Repositorio) -> None:
    mesa = _iniciada(repo)
    resposta = partida.jogar(repo, mesa, 9, 0, 2, 3)
    assert not resposta["aceita"]
    assert resposta["rodada"] == 6
    assert "0 a 4" in resposta["mensagem"]


def test_jogar_numa_casa_com_peca_gira_a_peca(repo: Repositorio) -> None:
    mesa = _iniciada(repo)
    resposta = partida.jogar(repo, mesa, 0, 0, 0, 1)
    assert resposta["aceita"]
    assert resposta["rodada"] == 7
    casa = next(c for c in resposta["casas"] if (c["linha"], c["coluna"]) == (0, 1))
    assert casa["saidas"] == "NS"


def test_passar_a_vez(repo: Repositorio) -> None:
    mesa = _iniciada(repo)
    resposta = partida.passar(repo, mesa)
    assert resposta["aceita"]
    assert resposta["rodada"] == 7
    assert resposta["resultado"] is None


def test_fim_grava_uma_vez_no_repositorio(repo: Repositorio) -> None:
    lido = repo.obter_jogador("novato")
    assert lido is not None
    antes = dataclasses.replace(lido)  # a memória devolve o próprio objeto, que muda ao gravar
    mesa = _iniciada(repo)
    partida.jogar(repo, mesa, 0, 0, 2, 3)
    resposta = _ate_o_fim(repo, mesa)

    resultado = resposta["resultado"]
    assert resultado is not None
    assert resultado["colocacao"] == 1
    assert resultado["pontos"] == 10
    assert resultado["fagulhas"] == 40
    assert resultado["rating_antes"] == antes.rating
    assert resultado["rating_depois"] == antes.rating + resultado["variacao_rating"]
    assert resultado["variacao_rating"] > 0

    depois = repo.obter_jogador("novato")
    assert depois is not None
    assert depois.partidas == antes.partidas + 1
    assert depois.vitorias == antes.vitorias + 1
    assert depois.fagulhas == antes.fagulhas + 40
    assert depois.rating == resultado["rating_depois"]
    assert repo.partidas_recentes("novato")[0].colocacao == 1

    # Ler, passar ou jogar de novo não grava outra vez.
    partida.ver(mesa)
    assert not partida.passar(repo, mesa)["aceita"]
    assert not partida.jogar(repo, mesa, 0, 0, 2, 3)["aceita"]
    final = repo.obter_jogador("novato")
    assert final is not None
    assert final.partidas == depois.partidas


def test_iniciar_de_novo_descarta_sem_gravar(repo: Repositorio) -> None:
    mesa = _iniciada(repo)
    partida.jogar(repo, mesa, 0, 0, 2, 3)
    resposta = partida.iniciar(repo, mesa, "voltz_br")
    assert resposta["apelido"] == "voltz_br"
    assert resposta["rodada"] == 6
    novato = repo.obter_jogador("novato")
    assert novato is not None
    assert novato.partidas == 2


def test_respostas_nao_trazem_email(repo: Repositorio) -> None:
    mesa = _iniciada(repo)
    textos = str(partida.ver(mesa)) + str(_ate_o_fim(repo, mesa))
    assert "@" not in textos
