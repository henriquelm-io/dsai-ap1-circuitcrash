"""Servidor MCP de ranking: a classificação e a posição de um jogador (spec 011, parte 1).

Rode com: uv run circuitcrash-mcp-ranking (o Claude Code inicia sozinho pelo .mcp.json).
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.domain.modelos import PARTIDAS_PARA_RANKING
from circuitcrash.mcps.comum import SO_LEITURA, buscar_por_apelido, repositorio_do_ambiente

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


def criar_servidor(repo: Repositorio | None = None) -> MCPServer:
    """Sem repositório, usa o do .env (o mesmo banco do site)."""
    dados = repo if repo is not None else repositorio_do_ambiente()
    servidor = MCPServer(
        "circuitcrash-ranking",
        instructions=(
            "Ranking do CircuitCrash, um jogo de puzzle de circuitos para 4 jogadores. "
            f"Só entram no ranking jogadores com pelo menos {PARTIDAS_PARA_RANKING} partidas. Só consulta."
        ),
    )

    @servidor.tool(name="ver_ranking", annotations=SO_LEITURA)
    def ver_ranking_(
        limite: Annotated[
            int, Field(description=f"Quantos jogadores mostrar, de 1 a {LIMITE_MAXIMO}.")
        ] = LIMITE_PADRAO,
    ) -> Ranking:
        """Mostra o ranking do CircuitCrash, do maior rating para o menor, com partidas e taxa de vitória."""
        return ver_ranking(dados, limite)

    @servidor.tool(name="posicao_do_jogador", annotations=SO_LEITURA)
    def posicao_do_jogador_(
        apelido: Annotated[str, Field(description="Apelido do jogador, como voltz_br (sem diferenciar maiúsculas).")],
    ) -> Posicao:
        """Diz a posição e o rating de um jogador no ranking, ou quantas partidas faltam para ele entrar."""
        return posicao_do_jogador(dados, apelido)

    return servidor


def main() -> None:
    criar_servidor().run("stdio")


if __name__ == "__main__":
    main()
