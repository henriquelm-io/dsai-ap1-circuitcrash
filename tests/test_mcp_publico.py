"""Servidor MCP público no /mcp do site, por HTTP (spec 012)."""

from typing import Any

import anyio
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from starlette.testclient import TestClient

from circuitcrash.app import criar_app
from circuitcrash.dados.memoria import RepositorioMemoria

TOOLS = {"ver_ranking", "posicao_do_jogador", "ver_partida", "iniciar_partida", "jogar_peca", "passar_vez"}


def _pelo_site(conversa: Any) -> tuple[Any, RepositorioMemoria]:
    """Roda a conversa com um cliente MCP falando HTTP com o app do site, com o lifespan ligado."""
    repo = RepositorioMemoria()
    app = criar_app(repo)

    async def rodar() -> Any:
        transporte = httpx2.ASGITransport(app=app)
        async with (
            app.router.lifespan_context(app),
            httpx2.AsyncClient(transport=transporte, base_url="http://circuitcrash.test") as http,
            Client(streamable_http_client("http://circuitcrash.test/mcp", http_client=http)) as cliente,
        ):
            return await conversa(cliente)

    return anyio.run(rodar), repo


def test_site_publica_as_seis_tools_e_o_ranking() -> None:
    async def conversa(cliente: Client) -> tuple[Any, Any]:
        ferramentas = (await cliente.list_tools()).tools
        return ferramentas, await cliente.call_tool("ver_ranking", {"limite": 2})

    (ferramentas, ranking), _ = _pelo_site(conversa)
    assert {f.name for f in ferramentas} == TOOLS
    assert [linha["apelido"] for linha in ranking.structured_content["jogadores"]] == ["ninacircuit", "lia.ohm"]


def test_site_joga_pelo_partida_id_sem_gravar() -> None:
    async def conversa(cliente: Client) -> Any:
        inicio = await cliente.call_tool("iniciar_partida", {"apelido": "luma_dev"})
        partida_id = inicio.structured_content["partida_id"]
        jogada = {"peca": 0, "giros": 0, "linha": 2, "coluna": 3, "partida_id": partida_id}
        await cliente.call_tool("jogar_peca", jogada)
        for _ in range(6):
            await cliente.call_tool("passar_vez", {"partida_id": partida_id})
        return await cliente.call_tool("ver_partida", {"partida_id": partida_id})

    final, repo = _pelo_site(conversa)
    assert final.structured_content["terminou"]
    assert not final.structured_content["resultado"]["gravado"]
    novato = repo.obter_jogador("novato")
    assert novato is not None
    assert novato.partidas == 2


def test_site_continua_respondendo_com_o_mcp() -> None:
    with TestClient(criar_app(RepositorioMemoria())) as cliente:
        assert cliente.get("/health").status_code == 200
        assert cliente.get("/ranking").status_code == 200
