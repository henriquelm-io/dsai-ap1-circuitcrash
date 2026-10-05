"""Contrato da camada de dados.

As telas só conversam com este Protocol. Hoje quem responde é o
RepositorioMemoria (dados de exemplo); a implementação com banco de dados
deve seguir exatamente estes métodos. Detalhes em docs/banco-de-dados.md.
"""

from __future__ import annotations

from typing import Protocol

from circuitcrash.domain.modelos import Avatar, Conquista, Jogador, Missao, ResumoPartida


class Repositorio(Protocol):
    # Jogadores
    def obter_jogador(self, jogador_id: str) -> Jogador | None: ...

    def listar_jogadores(self) -> list[Jogador]: ...

    def salvar_jogador(self, jogador: Jogador) -> None: ...

    def ranking(self, limite: int = 10) -> list[Jogador]:
        """Jogadores fora do período provisório, do maior rating para o menor."""
        ...

    # Avatares e inventário
    def listar_avatares(self) -> list[Avatar]: ...

    def obter_avatar(self, avatar_id: str) -> Avatar | None: ...

    def inventario(self, jogador_id: str) -> set[str]:
        """Ids dos avatares que o jogador possui."""
        ...

    def adicionar_ao_inventario(self, jogador_id: str, avatar_id: str) -> None: ...

    # Histórico e progresso
    def partidas_recentes(self, jogador_id: str, limite: int = 5) -> list[ResumoPartida]: ...

    def missoes_do_dia(self, jogador_id: str) -> list[Missao]: ...

    def conquistas(self, jogador_id: str) -> list[Conquista]: ...
