"""Repositório em memória com dados de exemplo.

Serve para desenvolver e apresentar as telas antes do banco existir.
Tudo é perdido quando o servidor reinicia.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date

from circuitcrash.domain.modelos import (
    Avatar,
    Conquista,
    Jogador,
    Missao,
    Raridade,
    ResultadoPartida,
    ResumoPartida,
)

AVATARES = [
    Avatar(
        "faisca",
        "Faísca",
        Raridade.COMUM,
        "A primeira centelha de todo circuito.",
        "#F5A524",
        "#3A2A0E",
        "M13 2 L4 14 H11 L10 22 L20 9 H13 Z",
    ),
    Avatar(
        "plug",
        "Plug",
        Raridade.COMUM,
        "Sempre conectado.",
        "#CBD5E1",
        "#1E293B",
        "M9 2v5 M15 2v5 M6 7h12v4a6 6 0 0 1-12 0z M12 17v5",
    ),
    Avatar(
        "onda",
        "Onda",
        Raridade.COMUM,
        "Corrente alternada, humor também.",
        "#5EEAD4",
        "#0F2A33",
        "M2 12 Q5 5 8 12 T14 12 T20 12 M20 12h2",
    ),
    Avatar(
        "resistor",
        "Resistor",
        Raridade.RARO,
        "Para quem controla a corrente com calma.",
        "#38BDF8",
        "#10233A",
        "M2 12h4 l2-5 3 10 3-10 3 10 2-5h5",
    ),
    Avatar(
        "chip",
        "Chip",
        Raridade.RARO,
        "Pensa rápido, aquece pouco.",
        "#A3E635",
        "#1B2E14",
        "M7 7h10v10H7z M10 3v4 M14 3v4 M10 17v4 M14 17v4 M3 10h4 M3 14h4 M17 10h4 M17 14h4",
    ),
    Avatar(
        "atomo",
        "Átomo",
        Raridade.EPICO,
        "Energia em estado puro.",
        "#C084FC",
        "#2A1840",
        "M3 12c0-2.8 4-5 9-5s9 2.2 9 5-4 5-9 5-9-2.2-9-5z M12 3c2.8 0 5 4 5 9s-2.2 9-5 9-5-4-5-9 2.2-9 5-9z",
    ),
    Avatar(
        "nucleo",
        "Núcleo",
        Raridade.LENDARIO,
        "O objetivo mais disputado do tabuleiro.",
        "#F472B6",
        "#3A1028",
        "M12 2 L21 7 V17 L12 22 L3 17 V7 Z M12 8 L16 10.5 V14.5 L12 17 L8 14.5 V10.5 Z",
    ),
    Avatar(
        "coroa",
        "Coroa",
        Raridade.EXCLUSIVO,
        "Prêmio do campeão de campeonato.",
        "#FCD34D",
        "#3A2A0E",
        "M3 18h18 M4 18 3 7l5 4 4-6 4 6 5-4-1 11",
    ),
]

JOGADORES = [
    Jogador(
        "veterano",
        "voltz_br",
        "voltz@exemplo.com",
        date(2026, 9, 1),
        fagulhas=320,
        rating=1482,
        partidas=48,
        vitorias=14,
        objetivos_capturados=112,
        avatar_id="faisca",
    ),
    Jogador(
        "novato",
        "luma_dev",
        "luma@exemplo.com",
        date(2026, 10, 3),
        fagulhas=60,
        rating=1200,
        partidas=2,
        vitorias=0,
        objetivos_capturados=1,
    ),
    Jogador(
        "lia",
        "lia.ohm",
        "lia@exemplo.com",
        date(2026, 8, 20),
        fagulhas=900,
        rating=1530,
        partidas=61,
        vitorias=22,
        objetivos_capturados=150,
        avatar_id="resistor",
    ),
    Jogador(
        "bruno",
        "brunovolt",
        "bruno@exemplo.com",
        date(2026, 9, 5),
        fagulhas=210,
        rating=1415,
        partidas=33,
        vitorias=8,
        objetivos_capturados=70,
        avatar_id="chip",
    ),
    Jogador(
        "kai",
        "kai_k",
        "kai@exemplo.com",
        date(2026, 9, 12),
        fagulhas=40,
        rating=1390,
        partidas=27,
        vitorias=5,
        objetivos_capturados=41,
    ),
    Jogador(
        "nina",
        "ninacircuit",
        "nina@exemplo.com",
        date(2026, 7, 30),
        fagulhas=1500,
        rating=1611,
        partidas=90,
        vitorias=37,
        objetivos_capturados=260,
        avatar_id="atomo",
    ),
]

INVENTARIOS = {
    "veterano": {"faisca", "plug"},
    "lia": {"resistor", "onda"},
    "bruno": {"chip"},
    "nina": {"atomo", "faisca", "coroa"},
}

PARTIDAS = {
    "veterano": [
        ResumoPartida(1, 14, +16, 60, "hoje"),
        ResumoPartida(3, 8, -4, 15, "hoje"),
        ResumoPartida(2, 11, +6, 25, "ontem"),
        ResumoPartida(4, 3, -12, 10, "ontem"),
        ResumoPartida(1, 17, +18, 40, "28/09"),
    ],
    "novato": [
        ResumoPartida(3, 6, 0, 35, "hoje"),
        ResumoPartida(4, 2, 0, 25, "ontem"),
    ],
}


class RepositorioMemoria:
    """Implementa circuitcrash.dados.repositorio.Repositorio sem banco."""

    def __init__(self) -> None:
        self._jogadores = {j.id: deepcopy(j) for j in JOGADORES}
        self._avatares = {a.id: a for a in AVATARES}
        self._inventarios = {k: set(v) for k, v in INVENTARIOS.items()}
        self._partidas = {k: list(v) for k, v in PARTIDAS.items()}
        self._contas_google: dict[str, str] = {}  # google_sub -> jogador_id

    def obter_jogador(self, jogador_id: str) -> Jogador | None:
        return self._jogadores.get(jogador_id)

    def listar_jogadores(self) -> list[Jogador]:
        return list(self._jogadores.values())

    def salvar_jogador(self, jogador: Jogador) -> None:
        self._jogadores[jogador.id] = jogador

    def ranking(self, limite: int = 10) -> list[Jogador]:
        elegiveis = [j for j in self._jogadores.values() if not j.provisorio]
        return sorted(elegiveis, key=lambda j: -j.rating)[:limite]

    def listar_avatares(self) -> list[Avatar]:
        return list(self._avatares.values())

    def obter_avatar(self, avatar_id: str) -> Avatar | None:
        return self._avatares.get(avatar_id)

    def inventario(self, jogador_id: str) -> set[str]:
        return set(self._inventarios.get(jogador_id, set()))

    def adicionar_ao_inventario(self, jogador_id: str, avatar_id: str) -> None:
        self._inventarios.setdefault(jogador_id, set()).add(avatar_id)

    def partidas_recentes(self, jogador_id: str, limite: int = 5) -> list[ResumoPartida]:
        return self._partidas.get(jogador_id, [])[:limite]

    def missoes_do_dia(self, jogador_id: str) -> list[Missao]:
        return [
            Missao("Jogue 2 partidas", 1, 2, 20),
            Missao("Capture 1 bateria", 0, 1, 30),
            Missao("Primeira vitória do dia", 0, 1, 20),
        ]

    def conquistas(self, jogador_id: str) -> list[Conquista]:
        jogador = self._jogadores.get(jogador_id)
        partidas = jogador.partidas if jogador else 0
        vitorias = jogador.vitorias if jogador else 0
        return [
            Conquista("Primeira faísca", min(partidas, 1), 1),
            Conquista("Eletricista", min(partidas, 25), 25),
            Conquista("Curto-circuito", 12 if partidas > 10 else 0, 20),
            Conquista("Caçador de núcleos", 7 if partidas > 10 else 0, 10),
            Conquista("Invicto", min(vitorias, 1), 5),
            Conquista("Campeão", 0, 1),
        ]

    def fagulhas_ganhas_hoje(self, jogador_id: str) -> int:
        return sum(p.fagulhas for p in self._partidas.get(jogador_id, []) if p.quando == "hoje")

    def registrar_partida(self, jogador_id: str, resultado: ResultadoPartida) -> None:
        jogador = self._jogadores.get(jogador_id)
        if jogador is None:
            raise ValueError(f"Jogador não encontrado: {jogador_id}.")
        resumo = ResumoPartida(
            resultado.colocacao, resultado.pontos, resultado.variacao_rating, resultado.fagulhas, "hoje"
        )
        self._partidas.setdefault(jogador_id, []).insert(0, resumo)
        jogador.fagulhas += resultado.fagulhas
        jogador.rating += resultado.variacao_rating
        jogador.partidas += 1
        jogador.vitorias += int(resultado.vitoria)
        jogador.objetivos_capturados += resultado.objetivos

    def obter_jogador_por_google(self, google_sub: str) -> Jogador | None:
        jogador_id = self._contas_google.get(google_sub)
        return self._jogadores.get(jogador_id) if jogador_id else None

    def obter_jogador_por_email(self, email: str) -> Jogador | None:
        alvo = email.strip().lower()
        return next((j for j in self._jogadores.values() if j.email.lower() == alvo), None)

    def criar_jogador_google(self, jogador: Jogador, google_sub: str) -> None:
        if google_sub in self._contas_google or jogador.id in self._jogadores:
            raise ValueError("Conta Google ou jogador já existe.")
        self._jogadores[jogador.id] = jogador
        self._contas_google[google_sub] = jogador.id

    def vincular_google(self, jogador_id: str, google_sub: str) -> bool:
        if jogador_id not in self._jogadores:
            return False
        atual = next((sub for sub, jid in self._contas_google.items() if jid == jogador_id), None)
        if atual is not None:
            return atual == google_sub
        if google_sub in self._contas_google:
            return False
        self._contas_google[google_sub] = jogador_id
        return True
