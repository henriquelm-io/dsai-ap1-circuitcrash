"""Consultas de ranking do servidor MCP: a classificação e a posição de um jogador (spec 011)."""

from __future__ import annotations

from typing import TypedDict

from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.domain.modelos import PARTIDAS_PARA_RANKING
from circuitcrash.mcps.comum import buscar_por_apelido

LIMITE_PADRAO = 10
LIMITE_MAXIMO = 50


class LinhaRanking(TypedDict):
    posicao: int
    apelido: str
    rating: int
    partidas: int
    vitorias: int
    taxa_vitoria: int


class Ranking(TypedDict):
    jogadores: list[LinhaRanking]
    total: int


class Posicao(TypedDict):
    encontrado: bool
    apelido: str
    posicao: int | None
    rating: int
    partidas: int
    provisorio: bool
    partidas_para_entrar: int
    mensagem: str


def ver_ranking(repo: Repositorio, limite: int = LIMITE_PADRAO) -> Ranking:
    limite = max(1, min(limite, LIMITE_MAXIMO))
    jogadores: list[LinhaRanking] = [
        {
            "posicao": i,
            "apelido": j.apelido,
            "rating": j.rating,
            "partidas": j.partidas,
            "vitorias": j.vitorias,
            "taxa_vitoria": j.taxa_vitoria,
        }
        for i, j in enumerate(repo.ranking(limite), start=1)
    ]
    return {"jogadores": jogadores, "total": len(jogadores)}


def posicao_do_jogador(repo: Repositorio, apelido: str) -> Posicao:
    jogador = buscar_por_apelido(repo, apelido)
    if jogador is None:
        return {
            "encontrado": False,
            "apelido": apelido.strip(),
            "posicao": None,
            "rating": 0,
            "partidas": 0,
            "provisorio": False,
            "partidas_para_entrar": 0,
            "mensagem": f"Nenhum jogador com o apelido {apelido.strip()!r}.",
        }
    # Mesma conta da tela /perfil.
    posicao = next((i for i, j in enumerate(repo.ranking(1000), start=1) if j.id == jogador.id), None)
    faltam = max(0, PARTIDAS_PARA_RANKING - jogador.partidas)
    if posicao is not None:
        mensagem = f"{jogador.apelido} está em {posicao}º no ranking, com rating {jogador.rating}."
    else:
        plural = "partida" if faltam == 1 else "partidas"
        mensagem = (
            f"{jogador.apelido} ainda está no período provisório (rating {jogador.rating}): "
            f"faltam {faltam} {plural} para entrar no ranking."
        )
    return {
        "encontrado": True,
        "apelido": jogador.apelido,
        "posicao": posicao,
        "rating": jogador.rating,
        "partidas": jogador.partidas,
        "provisorio": jogador.provisorio,
        "partidas_para_entrar": faltam,
        "mensagem": mensagem,
    }
