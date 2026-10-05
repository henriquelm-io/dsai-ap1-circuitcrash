"""Transforma o estado da partida em dados prontos para os templates (sem lógica de jogo)."""

from __future__ import annotations

from dataclasses import dataclass

from circuitcrash.domain.tabuleiro import (
    JOGADORES_DEMO,
    NOMES_FORMATO,
    OBJETIVOS,
    TAMANHO,
    Casa,
    EstadoPartida,
    TipoCasa,
)

PONTOS_BORDA = {"N": (50, 0), "E": (100, 50), "S": (50, 100), "W": (0, 50)}
COR_NEUTRA = "#475569"
COR_FONTE = "#E2E8F0"


def caminho(saidas: str) -> str:
    """Atributo d de um path SVG (viewBox 0 0 100 100) desenhando as saídas da peça."""
    if not saidas:
        return ""
    if len(saidas) == 1:
        x, y = PONTOS_BORDA[saidas]
        return f"M50 50 L{x} {y}"
    if len(saidas) == 2:
        (ax, ay), (bx, by) = PONTOS_BORDA[saidas[0]], PONTOS_BORDA[saidas[1]]
        if ax == bx or ay == by:
            return f"M{ax} {ay} L{bx} {by}"
        return f"M{ax} {ay} Q50 50 {bx} {by}"
    return " ".join(f"M50 50 L{x} {y}" for x, y in (PONTOS_BORDA[d] for d in saidas))


@dataclass(frozen=True)
class CasaVisao:
    linha: int
    coluna: int
    tipo: str
    caminho: str
    cor: str
    opacidade: float
    no_central: bool
    rotulo: str
    inicial: str = ""
    objetivo: str = ""
    pontos: str = ""
    cor_captura: str = COR_NEUTRA


def _rotulo(casa: Casa, linha: int, coluna: int) -> str:
    pos = f"linha {linha + 1}, coluna {coluna + 1}"
    if casa.tipo is TipoCasa.VAZIA:
        return f"Casa vazia, {pos}. Colocar peça aqui"
    if casa.tipo is TipoCasa.PECA and casa.dono is not None:
        return f"Peça de {JOGADORES_DEMO[casa.dono].nome}, {pos}. Girar"
    if casa.tipo is TipoCasa.FONTE:
        return "Fonte de energia"
    if casa.tipo is TipoCasa.BASE and casa.dono is not None:
        return f"Base de {JOGADORES_DEMO[casa.dono].nome}"
    if casa.tipo is TipoCasa.OBJETIVO and casa.objetivo:
        obj = OBJETIVOS[casa.objetivo]
        return f"{obj.nome}, {obj.pontos} pontos, {pos}"
    return f"Casa bloqueada, {pos}"


def casas(estado: EstadoPartida) -> list[CasaVisao]:
    resultado = []
    for linha in range(TAMANHO):
        for coluna in range(TAMANHO):
            casa = estado.casa(linha, coluna)
            cor = COR_NEUTRA
            if casa.dono is not None:
                cor = JOGADORES_DEMO[casa.dono].cor
            elif casa.tipo is TipoCasa.FONTE:
                cor = COR_FONTE
            energizada = (linha, coluna) in estado.energizados
            opacidade = 1.0 if energizada or casa.tipo is not TipoCasa.PECA else 0.45
            objetivo = OBJETIVOS[casa.objetivo] if casa.objetivo else None
            captor = casa.capturado_por
            resultado.append(
                CasaVisao(
                    linha=linha,
                    coluna=coluna,
                    tipo=casa.tipo.value,
                    caminho=caminho(casa.saidas) if casa.tipo in (TipoCasa.PECA, TipoCasa.BASE) else "",
                    cor=cor,
                    opacidade=opacidade,
                    no_central=casa.tipo is TipoCasa.PECA and len(casa.saidas) > 2,
                    rotulo=_rotulo(casa, linha, coluna),
                    inicial=JOGADORES_DEMO[casa.dono].inicial if casa.dono is not None else "",
                    objetivo=casa.objetivo or "",
                    pontos=f"+{objetivo.pontos}" if objetivo else "",
                    cor_captura=JOGADORES_DEMO[captor].cor if captor is not None else COR_NEUTRA,
                )
            )
    return resultado


@dataclass(frozen=True)
class PecaVisao:
    indice: int
    nome: str
    caminho: str
    selecionada: bool


def mao(estado: EstadoPartida) -> list[PecaVisao]:
    return [
        PecaVisao(i, NOMES_FORMATO[p.formato], caminho(p.saidas), i == estado.selecionada)
        for i, p in enumerate(estado.mao)
    ]
