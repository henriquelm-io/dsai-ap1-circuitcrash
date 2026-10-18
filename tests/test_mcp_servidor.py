"""Servidor MCP único, conversando pelo cliente MCP em processo (spec 011)."""

import json
from pathlib import Path
from typing import Any

import anyio
from mcp import Client

from circuitcrash.dados.memoria import RepositorioMemoria
from circuitcrash.mcps import servidor

LEITURA = {"ver_ranking", "posicao_do_jogador", "ver_partida"}
ESCRITA = {"iniciar_partida", "jogar_peca", "passar_vez"}
RAIZ = Path(__file__).resolve().parent.parent


def _conversar(
    chamadas: list[tuple[str, dict[str, Any]]], *, publico: bool = False
) -> tuple[list[Any], list[Any], RepositorioMemoria]:
    repo = RepositorioMemoria()
    mcp = servidor.criar_servidor(repo, publico=publico)

    async def conversa() -> tuple[list[Any], list[Any]]:
        async with Client(mcp) as cliente:
            ferramentas = (await cliente.list_tools()).tools
            resultados = [await cliente.call_tool(nome, argumentos) for nome, argumentos in chamadas]
            return ferramentas, resultados

    ferramentas, resultados = anyio.run(conversa)
    return ferramentas, resultados, repo


def test_seis_tools_tres_de_leitura_e_tres_de_escrita() -> None:
    ferramentas, _, _ = _conversar([])
    por_nome = {f.name: f for f in ferramentas}
    assert set(por_nome) == LEITURA | ESCRITA
    for nome in LEITURA:
        assert por_nome[nome].annotations.read_only_hint is True
    for nome in ESCRITA:
        assert por_nome[nome].annotations.read_only_hint is False
        assert por_nome[nome].annotations.destructive_hint is False


def test_docstrings_dizem_quando_usar() -> None:
    ferramentas, _, _ = _conversar([])
    for ferramenta in ferramentas:
        assert ferramenta.description
        assert "Use quando" in ferramenta.description, ferramenta.name


def test_consulta_o_ranking_pelo_cliente() -> None:
    _, (ranking, posicao), _ = _conversar(
        [("ver_ranking", {"limite": 2}), ("posicao_do_jogador", {"apelido": "luma_dev"})]
    )
    assert not ranking.is_error
    assert [linha["apelido"] for linha in ranking.structured_content["jogadores"]] == ["ninacircuit", "lia.ohm"]
    assert posicao.structured_content["partidas_para_entrar"] == 3


def test_uma_partida_inteira_pelo_cliente() -> None:
    chamadas: list[tuple[str, dict[str, Any]]] = [
        ("ver_partida", {}),
        ("iniciar_partida", {"apelido": "luma_dev"}),
        ("jogar_peca", {"peca": 0, "giros": 0, "linha": 2, "coluna": 3}),
    ]
    chamadas += [("passar_vez", {})] * 6
    chamadas.append(("ver_partida", {}))
    _, resultados, repo = _conversar(chamadas)

    assert all(not r.is_error for r in resultados)
    assert not resultados[0].structured_content["ativa"]
    assert resultados[1].structured_content["rodada"] == 6
    assert resultados[2].structured_content["aceita"]
    final = resultados[-1].structured_content
    assert final["terminou"]
    assert final["resultado"]["colocacao"] == 1
    assert "1º" in final["mensagem"]
    novato = repo.obter_jogador("novato")
    assert novato is not None
    assert novato.partidas == 3


def test_mcp_json_e_permissoes_do_projeto() -> None:
    mcp_json = json.loads((RAIZ / ".mcp.json").read_text(encoding="utf-8"))
    assert mcp_json["mcpServers"]["circuitcrash"]["args"] == ["run", "circuitcrash-mcp"]

    config = json.loads((RAIZ / ".claude" / "settings.json").read_text(encoding="utf-8"))
    permitidas = set(config["permissions"]["allow"])
    perguntar = set(config["permissions"]["ask"])
    assert permitidas == {f"mcp__circuitcrash__{nome}" for nome in LEITURA}
    assert perguntar == {f"mcp__circuitcrash__{nome}" for nome in ESCRITA}
    assert config["enabledMcpjsonServers"] == ["circuitcrash"]


def test_instrucoes_explicam_o_que_o_agente_errou_no_diario() -> None:
    # diario/2026-10-08.md: o agente achou que todos ganhavam o bônus e que os adversários jogavam.
    assert "o bônus é só seu" in servidor.INSTRUCOES
    assert "não jogam" in servidor.INSTRUCOES
    assert "não se perdem" in servidor.INSTRUCOES


def _publico() -> tuple[Any, RepositorioMemoria]:
    repo = RepositorioMemoria()
    return servidor.criar_servidor(repo, publico=True), repo


def test_servidor_publico_separa_as_partidas_pelo_id() -> None:
    # Spec 012: o protocolo não tem sessão; cada pessoa leva o partida_id da sua partida.
    mcp, _ = _publico()

    async def conversa() -> tuple[Any, Any, Any, Any]:
        async with Client(mcp) as ana, Client(mcp) as beto:
            da_ana = (await ana.call_tool("iniciar_partida", {"apelido": "luma_dev"})).structured_content
            do_beto = (await beto.call_tool("iniciar_partida", {"apelido": "voltz_br"})).structured_content
            jogada = {"peca": 0, "giros": 0, "linha": 2, "coluna": 3, "partida_id": da_ana["partida_id"]}
            await ana.call_tool("jogar_peca", jogada)
            return (
                da_ana,
                do_beto,
                await ana.call_tool("ver_partida", {"partida_id": da_ana["partida_id"]}),
                await beto.call_tool("ver_partida", {"partida_id": do_beto["partida_id"]}),
            )

    da_ana, do_beto, ver_ana, ver_beto = anyio.run(conversa)
    assert da_ana["partida_id"] and do_beto["partida_id"]
    assert da_ana["partida_id"] != do_beto["partida_id"]
    assert da_ana["partida_id"] in da_ana["mensagem"]
    assert (ver_ana.structured_content["apelido"], ver_ana.structured_content["rodada"]) == ("luma_dev", 7)
    assert (ver_beto.structured_content["apelido"], ver_beto.structured_content["rodada"]) == ("voltz_br", 6)


def test_servidor_publico_sem_id_ou_com_id_desconhecido_responde_sem_erro() -> None:
    _, resultados, _ = _conversar(
        [
            ("iniciar_partida", {"apelido": "luma_dev"}),
            ("ver_partida", {}),
            ("passar_vez", {}),
            ("jogar_peca", {"peca": 0, "giros": 0, "linha": 2, "coluna": 3, "partida_id": "inventado"}),
        ],
        publico=True,
    )
    _, sem_id, passar_sem_id, desconhecido = resultados
    for resultado in (sem_id, passar_sem_id, desconhecido):
        assert not resultado.is_error
        assert not resultado.structured_content["ativa"]
        assert "iniciar_partida" in resultado.structured_content["mensagem"]
    assert "partida_id" in sem_id.structured_content["mensagem"]
    assert "'inventado' não encontrada" in desconhecido.structured_content["mensagem"]


def test_servidor_publico_avisa_que_nao_grava_e_pede_o_id() -> None:
    ferramentas, _, _ = _conversar([], publico=True)
    por_nome = {f.name: f for f in ferramentas}
    assert "não é gravado" in (por_nome["iniciar_partida"].description or "")
    assert "partida_id" in (por_nome["iniciar_partida"].description or "")
    for nome in ("ver_partida", "jogar_peca", "passar_vez"):
        assert "partida_id" in por_nome[nome].input_schema["properties"], nome
    publicas = servidor.instrucoes(publico=True)
    assert "não é gravado" in publicas
    assert "partida_id" in publicas
    assert "o bônus é só seu" in publicas
    assert "não é gravado" not in servidor.INSTRUCOES


def test_partida_inteira_no_servidor_publico_nao_grava() -> None:
    mcp, repo = _publico()

    async def conversa() -> Any:
        async with Client(mcp) as cliente:
            inicio = await cliente.call_tool("iniciar_partida", {"apelido": "luma_dev"})
            partida_id = inicio.structured_content["partida_id"]
            jogada = {"peca": 0, "giros": 0, "linha": 2, "coluna": 3, "partida_id": partida_id}
            await cliente.call_tool("jogar_peca", jogada)
            for _ in range(6):
                await cliente.call_tool("passar_vez", {"partida_id": partida_id})
            return await cliente.call_tool("ver_partida", {"partida_id": partida_id})

    final = anyio.run(conversa).structured_content
    assert final["terminou"]
    assert final["resultado"]["colocacao"] == 1
    assert not final["resultado"]["gravado"]
    assert "não grava" in final["mensagem"]
    novato = repo.obter_jogador("novato")
    assert novato is not None
    assert novato.partidas == 2
