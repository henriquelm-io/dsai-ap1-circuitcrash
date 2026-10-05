"""Fagulhas e rating ao fim da partida (spec 006).

Python puro: sem banco, sem rede, sem relógio. Quem chama informa quantas
Fagulhas o jogador já ganhou hoje e os ratings dos adversários.
"""

from __future__ import annotations

from collections.abc import Sequence

from circuitcrash.domain.modelos import Jogador, ResultadoPartida, TipoPartida

RECOMPENSA_COLOCACAO = {1: 40, 2: 25, 3: 15, 4: 10}
LIMITE_DIARIO_FAGULHAS = 400
# Os adversários da demonstração não são contas de jogadores: valem o rating inicial.
RATING_ADVERSARIO_PADRAO = 1200
K_PROVISORIO = 48
K_NORMAL = 32


def fagulhas_da_colocacao(colocacao: int, tipo: TipoPartida) -> int:
    """Fagulhas pela colocação, antes do limite diário. Casual vale metade, para baixo."""
    if colocacao not in RECOMPENSA_COLOCACAO:
        raise ValueError(f"Colocação inválida: {colocacao}.")
    base = RECOMPENSA_COLOCACAO[colocacao]
    return base // 2 if tipo is TipoPartida.CASUAL else base


def aplicar_limite(ganho: int, ja_ganhas_hoje: int) -> int:
    """Corta o ganho no que falta para o limite do dia; nunca fica negativo."""
    return max(0, min(ganho, LIMITE_DIARIO_FAGULHAS - ja_ganhas_hoje))


def esperado(meu_rating: int, rating_adversario: int) -> float:
    """Chance esperada de ficar à frente do adversário, pelo Elo."""
    return 1 / (1 + 10 ** ((rating_adversario - meu_rating) / 400))


def variacao_elo(meu_rating: int, meus_pontos: int, adversarios: Sequence[tuple[int, int]], provisorio: bool) -> int:
    """Variação de rating contra vários adversários, cada um dado por (rating, pontos).

    Contra cada adversário: 1 se fiz mais pontos, 0,5 se empatamos, 0 se fiz menos.
    O K é dividido pelo número de adversários, para uma partida de 4 valer tanto
    quanto uma de 2.
    """
    if not adversarios:
        return 0
    soma = 0.0
    for rating, pontos in adversarios:
        resultado = 1.0 if meus_pontos > pontos else 0.5 if meus_pontos == pontos else 0.0
        soma += resultado - esperado(meu_rating, rating)
    k = K_PROVISORIO if provisorio else K_NORMAL
    return round(k / len(adversarios) * soma)


def resultado_da_partida(
    jogador: Jogador,
    tipo: TipoPartida,
    colocacao: int,
    pontos: int,
    objetivos: int,
    adversarios: Sequence[tuple[int, int]],
    ja_ganhas_hoje: int,
) -> ResultadoPartida:
    """Calcula o que a partida terminada muda no perfil do jogador."""
    ganho = fagulhas_da_colocacao(colocacao, tipo)
    fagulhas = aplicar_limite(ganho, ja_ganhas_hoje)

    variacao = 0
    if tipo is TipoPartida.RANQUEADA:
        variacao = variacao_elo(jogador.rating, pontos, adversarios, jogador.provisorio)
        # Com empate de pontos, o Elo puro poderia tirar rating do 1º ou dar ao último.
        if colocacao == 1:
            variacao = max(0, variacao)
        elif colocacao == len(adversarios) + 1:
            variacao = min(0, variacao)

    return ResultadoPartida(
        tipo=tipo,
        colocacao=colocacao,
        pontos=pontos,
        objetivos=objetivos,
        rating_antes=jogador.rating,
        variacao_rating=variacao,
        fagulhas=fagulhas,
        limite_atingido=fagulhas < ganho,
    )
