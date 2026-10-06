import pytest

from circuitcrash.domain import adversarios as a
from circuitcrash.domain import tabuleiro as t


def _jogar_como_humano(estado: t.EstadoPartida) -> None:
    """O jogador 0 joga pela mesma estratégia, pela API da tela."""
    jogada = a.escolher_jogada(estado, 0)
    if jogada.tipo is a.TipoJogada.PASSAR:
        t.passar(estado)
        return
    if jogada.tipo is a.TipoJogada.COLOCAR:
        t.selecionar(estado, jogada.indice)
        estado.mao[jogada.indice].saidas = jogada.saidas
    assert t.jogar_na_casa(estado, jogada.linha, jogada.coluna)


def _partida_completa(semente: int, humano_joga: bool = True) -> t.EstadoPartida:
    estado = t.nova_partida(semente)
    estado.rodada = 1
    while not estado.terminou:
        if humano_joga:
            _jogar_como_humano(estado)
        else:
            t.passar(estado)
    return estado


def _retrato(estado: t.EstadoPartida) -> tuple[object, ...]:
    casas = tuple((c.tipo, c.saidas, c.dono, c.capturado_por) for linha in estado.casas for c in linha)
    maos = tuple((j, tuple((p.formato, p.saidas) for p in m)) for j, m in sorted(estado.maos_adversarios.items()))
    return (casas, tuple(estado.pontos), tuple(estado.historico), maos, estado.rodada)


@pytest.mark.parametrize("semente", [1, 7, 42, 2026])
def test_adversario_nunca_faz_jogada_invalida(semente: int, monkeypatch: pytest.MonkeyPatch) -> None:
    escolher = a.escolher_jogada
    conferidas = []

    def escolher_e_conferir(estado: t.EstadoPartida, jogador: int) -> a.Jogada:
        jogada = escolher(estado, jogador)
        assert jogador in t.ADVERSARIOS
        assert jogada in a.jogadas_validas(estado, jogador)
        assert a.eh_valida(estado, jogador, jogada)
        if jogada.tipo is a.TipoJogada.COLOCAR:
            assert estado.casa(jogada.linha, jogada.coluna).tipo is t.TipoCasa.VAZIA
        conferidas.append(jogada)
        return jogada

    monkeypatch.setattr(a, "escolher_jogada", escolher_e_conferir)
    estado = t.nova_partida(semente)
    estado.rodada = 1
    while not estado.terminou:
        # O humano joga pela estratégia original, sem passar pela conferência.
        jogada = escolher(estado, 0)
        if jogada.tipo is a.TipoJogada.COLOCAR:
            t.selecionar(estado, jogada.indice)
            estado.mao[jogada.indice].saidas = jogada.saidas
            assert t.jogar_na_casa(estado, jogada.linha, jogada.coluna)
        elif jogada.tipo is a.TipoJogada.GIRAR:
            assert t.jogar_na_casa(estado, jogada.linha, jogada.coluna)
        else:
            t.passar(estado)
    assert len(conferidas) == 3 * t.MAX_RODADAS
    for jogador in t.ADVERSARIOS:
        assert len(estado.maos_adversarios[jogador]) == t.TAMANHO_MAO


def test_peca_colocada_pelo_adversario_fica_no_circuito_dele() -> None:
    estado = t.nova_partida()
    jogada = a.escolher_jogada(estado, 2)
    assert jogada.tipo is a.TipoJogada.COLOCAR
    a.aplicar(estado, 2, jogada)
    circuito, _, _ = t.circuito_do_jogador(estado, 2)
    assert (jogada.linha, jogada.coluna) in circuito
    assert estado.casa(jogada.linha, jogada.coluna).dono == 2


def test_aplicar_recusa_jogada_invalida() -> None:
    estado = t.nova_partida()
    with pytest.raises(ValueError):
        a.aplicar(estado, 1, a.Jogada(a.TipoJogada.COLOCAR, 6, 3, 0, "NS"))  # solta, longe da Lia
    with pytest.raises(ValueError):
        a.aplicar(estado, 1, a.Jogada(a.TipoJogada.GIRAR, 4, 1))  # peça do Bruno


def test_prefere_capturar_objetivo() -> None:
    estado = t.nova_partida()
    # Bruno: a peça (4,3) passa a ter saída para baixo; uma curva em (5,3) toca o Núcleo (5).
    estado.casa(4, 3).saidas = "NSW"
    estado.maos_adversarios[2] = [t.PecaMao("reta", "NS"), t.PecaMao("curva", "SW")]
    jogada = a.escolher_jogada(estado, 2)
    assert (jogada.tipo, jogada.linha, jogada.coluna) == (a.TipoJogada.COLOCAR, 5, 3)
    texto = a.aplicar(estado, 2, jogada)
    assert texto == "Bruno colocou uma curva; Bruno capturou Núcleo (+5)"
    assert estado.pontos[2] == 6 + 5


def test_coloca_para_chegar_mais_perto_da_fonte() -> None:
    estado = t.nova_partida()
    # Só sobram as peças do Kai; sem o isolante, há caminho da base dele até a fonte.
    for linha in estado.casas:
        for coluna, casa in enumerate(linha):
            if casa.tipo is t.TipoCasa.BLOQUEIO or (casa.tipo is t.TipoCasa.PECA and casa.dono != 3):
                linha[coluna] = t.Casa()
    t.recalcular(estado, pontuar=False)
    estado.maos_adversarios[3] = [t.PecaMao("reta", "EW")]
    antes = a.distancia_do_alvo(estado, 3)
    jogada = a.escolher_jogada(estado, 3)
    assert jogada == a.Jogada(a.TipoJogada.COLOCAR, 5, 6, 0, "NS")
    assert a.aplicar(estado, 3, jogada) == "Kai colocou uma reta"
    assert a.distancia_do_alvo(estado, 3) == antes - 1


def test_gira_a_propria_peca_para_religar_o_circuito() -> None:
    estado = t.nova_partida()
    estado.casa(3, 4).saidas = "SW"  # a curva da Lia junto da fonte foi girada por alguém
    assert not t.circuito_do_jogador(estado, 1)[1]
    estado.maos_adversarios[1] = []
    jogada = a.escolher_jogada(estado, 1)
    assert jogada == a.Jogada(a.TipoJogada.GIRAR, 3, 4)


def test_passa_quando_nada_ajuda() -> None:
    estado = t.nova_partida()
    # Kai está travado: nenhum caminho por casas vazias até a fonte.
    assert a.distancia_do_alvo(estado, 3) == a.SEM_CAMINHO
    assert a.escolher_jogada(estado, 3) == a.PASSAR
    assert a.aplicar(estado, 3, a.PASSAR) == "Kai passou a vez"


def test_mesma_semente_mesma_partida() -> None:
    assert _retrato(_partida_completa(7)) == _retrato(_partida_completa(7))
    assert _retrato(_partida_completa(42, humano_joga=False)) == _retrato(_partida_completa(42, humano_joga=False))


def test_semente_muda_as_maos_dos_adversarios() -> None:
    maos = {
        semente: [(p.formato, p.saidas) for p in t.nova_partida(semente).maos_adversarios[1]] for semente in range(5)
    }
    assert len({tuple(m) for m in maos.values()}) > 1


def test_partida_de_12_rodadas_termina_com_classificacao() -> None:
    estado = t.nova_partida(2026)
    estado.rodada = 1
    jogadas = 0
    linhas_dos_adversarios: set[str] = set()
    while not estado.terminou:
        _jogar_como_humano(estado)
        jogadas += 1
        linhas_dos_adversarios |= {linha.split()[0] for linha in estado.historico[:3]}
    assert jogadas == t.MAX_RODADAS
    assert linhas_dos_adversarios == {"Lia", "Bruno", "Kai"}
    classificacao = t.classificacao(estado)
    assert [c for c, _, _ in classificacao] == [1, 2, 3, 4]
    assert {j.indice for _, j, _ in classificacao} == {0, 1, 2, 3}
    assert [p for _, _, p in classificacao] == sorted(estado.pontos, reverse=True)
    assert estado.mensagem == "Fim de partida!"
