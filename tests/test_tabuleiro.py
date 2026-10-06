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


def test_jogada_aceita_aciona_os_tres_adversarios_e_avanca_uma_rodada() -> None:
    estado = t.nova_partida()
    t.passar(estado)
    assert estado.rodada == 7
    assert [linha.split()[0] for linha in estado.historico[:4]] == ["Kai", "Bruno", "Lia", "Você"]


def test_jogada_recusada_nao_aciona_os_adversarios() -> None:
    estado = t.nova_partida()
    historico = list(estado.historico)
    assert not t.jogar_na_casa(estado, 5, 5)
    assert estado.historico == historico
    assert estado.rodada == 6


def test_cada_adversario_tem_a_propria_mao() -> None:
    estado = t.nova_partida()
    assert sorted(estado.maos_adversarios) == [1, 2, 3]
    assert all(len(m) == t.TAMANHO_MAO for m in estado.maos_adversarios.values())
    assert all(m is not estado.mao for m in estado.maos_adversarios.values())


def test_bonus_final_vale_para_todo_circuito_energizado() -> None:
    estado = t.nova_partida()
    estado.rodada = t.MAX_RODADAS
    estado.maos_adversarios = {j: [] for j in t.ADVERSARIOS}  # ninguém coloca peça na última rodada
    t.passar(estado)
    assert estado.terminou
    assert estado.pontos == [4, 9 + t.BONUS_ENERGIZADO, 6 + t.BONUS_ENERGIZADO, 3]
