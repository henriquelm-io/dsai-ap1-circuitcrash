"""Entidades da plataforma (jogadores, avatares, partidas). Sem dependência de banco."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

PARTIDAS_PARA_RANKING = 5


class Raridade(StrEnum):
    COMUM = "comum"
    RARO = "raro"
    EPICO = "epico"
    LENDARIO = "lendario"
    EXCLUSIVO = "exclusivo"

    @property
    def rotulo(self) -> str:
        return {
            "comum": "Comum",
            "raro": "Raro",
            "epico": "Épico",
            "lendario": "Lendário",
            "exclusivo": "Exclusivo",
        }[self.value]


PRECOS = {
    Raridade.COMUM: 150,
    Raridade.RARO: 400,
    Raridade.EPICO: 900,
    Raridade.LENDARIO: 2000,
}


@dataclass(frozen=True)
class Avatar:
    id: str
    nome: str
    raridade: Raridade
    descricao: str
    cor: str
    fundo: str
    desenho: str  # atributo "d" de um <path> SVG, viewBox 0 0 24 24

    @property
    def preco(self) -> int | None:
        """None para avatares exclusivos, que não são vendidos."""
        return PRECOS.get(self.raridade)


@dataclass
class Jogador:
    id: str
    apelido: str
    email: str
    membro_desde: date
    fagulhas: int = 0
    rating: int = 1200
    partidas: int = 0
    vitorias: int = 0
    objetivos_capturados: int = 0
    avatar_id: str | None = None

    @property
    def inicial(self) -> str:
        return self.apelido[:1].upper()

    @property
    def provisorio(self) -> bool:
        return self.partidas < PARTIDAS_PARA_RANKING

    @property
    def taxa_vitoria(self) -> int:
        return round(100 * self.vitorias / self.partidas) if self.partidas else 0


@dataclass(frozen=True)
class ResumoPartida:
    colocacao: int
    pontos: int
    variacao_rating: int
    fagulhas: int
    quando: str


@dataclass(frozen=True)
class Missao:
    titulo: str
    progresso: int
    meta: int
    recompensa: int

    @property
    def concluida(self) -> bool:
        return self.progresso >= self.meta


@dataclass(frozen=True)
class Conquista:
    nome: str
    progresso: int
    meta: int

    @property
    def concluida(self) -> bool:
        return self.progresso >= self.meta


class TipoPartida(StrEnum):
    RANQUEADA = "ranqueada"
    CASUAL = "casual"


@dataclass(frozen=True)
class ResultadoPartida:
    """O que uma partida terminada muda no perfil do jogador (spec 006)."""

    tipo: TipoPartida
    colocacao: int
    pontos: int
    objetivos: int
    rating_antes: int
    variacao_rating: int
    fagulhas: int
    limite_atingido: bool

    @property
    def rating_depois(self) -> int:
        return self.rating_antes + self.variacao_rating

    @property
    def vitoria(self) -> bool:
        return self.colocacao == 1
