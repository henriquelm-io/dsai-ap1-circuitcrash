from circuitcrash.domain import tabuleiro as t


def test_girar_quatro_vezes_volta_ao_inicio() -> None:
    assert t.girar("NE", 4) == "NE"
    assert t.girar("NE") == "ES"
    assert t.girar("NS") == "EW"


def test_partida_demo_comeca_com_lia_e_bruno_energizados() -> None:
    estado = t.nova_partida()
    energizados = [t.circuito_do_jogador(estado, i)[1] for i in range(4)]
    assert energizados == [False, True, True, False]


def test_colocar_curva_energiza_e_captura_bateria() -> None:
    estado = t.nova_partida()
    assert t.jogar_na_casa(estado, 2, 3)
    assert t.circuito_do_jogador(estado, 0)[1]
    assert estado.pontos[0] == 4 + 3
    assert estado.rodada == 7


def test_peca_solta_e_recusada() -> None:
    estado = t.nova_partida()
    assert not t.jogar_na_casa(estado, 5, 5)
    assert estado.erro
    assert estado.rodada == 6


def test_casa_ocupada_por_objetivo_e_recusada() -> None:
    estado = t.nova_partida()
    assert not t.jogar_na_casa(estado, 1, 4)


def test_girar_peca_adversaria_corta_energia() -> None:
    estado = t.nova_partida()
    assert t.jogar_na_casa(estado, 3, 4)  # gira a curva da Lia
    assert not t.circuito_do_jogador(estado, 1)[1]


def test_partida_termina_depois_da_rodada_12() -> None:
    estado = t.nova_partida()
    for _ in range(t.MAX_RODADAS):
        t.passar(estado)
    assert estado.terminou
    assert [c for c, _, _ in t.classificacao(estado)] == [1, 2, 3, 4]


def test_mesma_semente_mesma_mao() -> None:
    assert [p.saidas for p in t.nova_partida().mao] == [p.saidas for p in t.nova_partida().mao]
