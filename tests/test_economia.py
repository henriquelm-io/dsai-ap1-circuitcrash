from datetime import date

import pytest

from circuitcrash.domain import economia
from circuitcrash.domain.economia import (
    K_NORMAL,
    LIMITE_DIARIO_FAGULHAS,
    RATING_ADVERSARIO_PADRAO,
    aplicar_limite,
    esperado,
    fagulhas_da_colocacao,
    resultado_da_partida,
    variacao_elo,
)
from circuitcrash.domain.modelos import Jogador, TipoPartida

RANQUEADA = TipoPartida.RANQUEADA
CASUAL = TipoPartida.CASUAL


def jogador(rating: int = 1200, partidas: int = 20) -> Jogador:
    return Jogador("j", "j", "j@exemplo.com", date(2026, 1, 1), rating=rating, partidas=partidas)


def iguais(*pontos: int) -> list[tuple[int, int]]:
    """Adversários com o rating padrão e os pontos dados."""
    return [(RATING_ADVERSARIO_PADRAO, p) for p in pontos]


# ---------- Fagulhas ----------


@pytest.mark.parametrize(("colocacao", "fagulhas"), [(1, 40), (2, 25), (3, 15), (4, 10)])
def test_ranqueada_paga_pela_colocacao(colocacao: int, fagulhas: int) -> None:
    assert fagulhas_da_colocacao(colocacao, RANQUEADA) == fagulhas


@pytest.mark.parametrize(("colocacao", "fagulhas"), [(1, 20), (2, 12), (3, 7), (4, 5)])
def test_casual_paga_metade_para_baixo(colocacao: int, fagulhas: int) -> None:
    assert fagulhas_da_colocacao(colocacao, CASUAL) == fagulhas


@pytest.mark.parametrize("colocacao", [0, 5, -1])
def test_colocacao_invalida(colocacao: int) -> None:
    with pytest.raises(ValueError):
        fagulhas_da_colocacao(colocacao, RANQUEADA)


@pytest.mark.parametrize(
    ("ganho", "ja_ganhas", "recebe"),
    [
        (40, 0, 40),
        (40, 360, 40),
        (40, 380, 20),
        (40, 400, 0),
        (40, 450, 0),
        (0, 0, 0),
    ],
)
def test_limite_diario(ganho: int, ja_ganhas: int, recebe: int) -> None:
    assert aplicar_limite(ganho, ja_ganhas) == recebe


def test_limite_diario_e_400() -> None:
    assert LIMITE_DIARIO_FAGULHAS == 400


# ---------- Elo ----------


def test_esperado_com_ratings_iguais_e_meio() -> None:
    assert esperado(1200, 1200) == pytest.approx(0.5)


def test_esperado_e_simetrico() -> None:
    assert esperado(1400, 1200) + esperado(1200, 1400) == pytest.approx(1.0)
    assert esperado(1400, 1200) > 0.5


def test_esperado_com_400_de_diferenca() -> None:
    assert esperado(1600, 1200) == pytest.approx(10 / 11)


def test_primeiro_sobe_e_ultimo_desce_com_ratings_iguais() -> None:
    assert variacao_elo(1200, 10, iguais(8, 6, 4), provisorio=False) == 16
    assert variacao_elo(1200, 2, iguais(8, 6, 4), provisorio=False) == -16


def test_segundo_e_terceiro_com_ratings_iguais() -> None:
    assert variacao_elo(1200, 7, iguais(8, 6, 4), provisorio=False) == round(K_NORMAL / 3 * 0.5)
    assert variacao_elo(1200, 5, iguais(8, 6, 4), provisorio=False) == -round(K_NORMAL / 3 * 0.5)


def test_vencer_adversarios_fortes_rende_mais() -> None:
    fortes = [(1500, 1), (1500, 1), (1500, 1)]
    fracos = [(900, 1), (900, 1), (900, 1)]
    assert variacao_elo(1200, 10, fortes, provisorio=False) > variacao_elo(1200, 10, fracos, provisorio=False)


def test_perder_para_adversarios_fracos_custa_mais() -> None:
    fortes = [(1500, 9), (1500, 9), (1500, 9)]
    fracos = [(900, 9), (900, 9), (900, 9)]
    assert variacao_elo(1200, 1, fracos, provisorio=False) < variacao_elo(1200, 1, fortes, provisorio=False)


def test_provisorio_muda_mais() -> None:
    normal = variacao_elo(1200, 10, iguais(8, 6, 4), provisorio=False)
    provisorio = variacao_elo(1200, 10, iguais(8, 6, 4), provisorio=True)
    assert provisorio == 24
    assert provisorio > normal


def test_empate_de_pontos_conta_meio() -> None:
    assert variacao_elo(1200, 5, iguais(5, 5, 5), provisorio=False) == 0


def test_sem_adversarios_nao_muda() -> None:
    assert variacao_elo(1200, 5, [], provisorio=False) == 0


def test_mesma_entrada_mesmo_resultado() -> None:
    adversarios = [(1350, 9), (1180, 4), (1420, 7)]
    assert variacao_elo(1390, 8, adversarios, False) == variacao_elo(1390, 8, adversarios, False)


# ---------- resultado da partida ----------


def test_resultado_do_primeiro_lugar() -> None:
    r = resultado_da_partida(jogador(1390), RANQUEADA, 1, 14, 2, iguais(9, 6, 3), ja_ganhas_hoje=75)
    assert r.fagulhas == 40
    assert not r.limite_atingido
    assert r.rating_antes == 1390
    assert r.variacao_rating > 0
    assert r.rating_depois == 1390 + r.variacao_rating
    assert r.vitoria
    assert (r.colocacao, r.pontos, r.objetivos) == (1, 14, 2)


def test_resultado_do_ultimo_lugar() -> None:
    r = resultado_da_partida(jogador(), RANQUEADA, 4, 3, 0, iguais(9, 6, 4), ja_ganhas_hoje=0)
    assert r.fagulhas == 10
    assert r.variacao_rating == -16
    assert not r.vitoria


def test_resultado_corta_no_limite_e_avisa() -> None:
    r = resultado_da_partida(jogador(), RANQUEADA, 1, 14, 0, iguais(9, 6, 3), ja_ganhas_hoje=390)
    assert r.fagulhas == 10
    assert r.limite_atingido


def test_resultado_com_limite_ja_estourado() -> None:
    r = resultado_da_partida(jogador(), RANQUEADA, 2, 9, 0, iguais(14, 6, 3), ja_ganhas_hoje=400)
    assert r.fagulhas == 0
    assert r.limite_atingido


def test_ganho_que_chega_exato_ao_limite_nao_avisa() -> None:
    r = resultado_da_partida(jogador(), RANQUEADA, 1, 14, 0, iguais(9, 6, 3), ja_ganhas_hoje=360)
    assert r.fagulhas == 40
    assert not r.limite_atingido


def test_casual_nao_muda_rating_e_paga_metade() -> None:
    r = resultado_da_partida(jogador(), CASUAL, 1, 14, 0, iguais(9, 6, 3), ja_ganhas_hoje=0)
    assert r.variacao_rating == 0
    assert r.fagulhas == 20
    assert r.tipo is CASUAL


def test_provisorio_usa_k_maior() -> None:
    novato = resultado_da_partida(jogador(partidas=2), RANQUEADA, 1, 14, 0, iguais(9, 6, 3), 0)
    veterano = resultado_da_partida(jogador(partidas=20), RANQUEADA, 1, 14, 0, iguais(9, 6, 3), 0)
    assert novato.variacao_rating > veterano.variacao_rating


def test_primeiro_nunca_perde_rating_mesmo_empatado() -> None:
    # Empatado em pontos com um adversário muito mais forte: o Elo puro daria negativo.
    r = resultado_da_partida(jogador(1800), RANQUEADA, 1, 10, 0, [(1200, 10), (1200, 10), (1200, 10)], 0)
    assert r.variacao_rating == 0


def test_ultimo_nunca_ganha_rating_mesmo_empatado() -> None:
    r = resultado_da_partida(jogador(800), RANQUEADA, 4, 3, 0, [(1500, 3), (1500, 3), (1500, 3)], 0)
    assert r.variacao_rating == 0


def test_resultado_com_colocacao_invalida() -> None:
    with pytest.raises(ValueError):
        resultado_da_partida(jogador(), RANQUEADA, 5, 0, 0, iguais(9, 6, 3), 0)


def test_economia_nao_depende_de_dados() -> None:
    fonte = economia.__file__
    with open(fonte, encoding="utf-8") as arquivo:
        codigo = arquivo.read()
    assert "circuitcrash.dados" not in codigo
    assert "datetime" not in codigo
