"""Servidor MCP de ranking (spec 011, parte 1)."""

from typing import Any

import anyio
from mcp import Client

from circuitcrash.dados.memoria import RepositorioMemoria
from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.mcps import ranking


def test_ranking_na_mesma_ordem_da_tela(repo: Repositorio) -> None:
    resposta = ranking.ver_ranking(repo)
    apelidos = [linha["apelido"] for linha in resposta["jogadores"]]
    assert apelidos == [j.apelido for j in repo.ranking(ranking.LIMITE_PADRAO)]
    assert apelidos[:3] == ["ninacircuit", "lia.ohm", "voltz_br"]
    assert [linha["posicao"] for linha in resposta["jogadores"]] == list(range(1, len(apelidos) + 1))
    assert resposta["total"] == len(apelidos)


def test_linha_do_ranking_traz_os_numeros_do_jogador(repo: Repositorio) -> None:
    primeiro = ranking.ver_ranking(repo, 1)["jogadores"][0]
    assert primeiro == {
        "posicao": 1,
        "apelido": "ninacircuit",
        "rating": 1611,
        "partidas": 90,
        "vitorias": 37,
        "taxa_vitoria": 41,
    }


def test_limite_e_ajustado_entre_1_e_50(repo: Repositorio) -> None:
    assert ranking.ver_ranking(repo, 2)["total"] == 2
    assert ranking.ver_ranking(repo, 0)["total"] == 1
    assert ranking.ver_ranking(repo, -5)["total"] == 1
    assert ranking.ver_ranking(repo, 1000)["total"] == len(repo.ranking(ranking.LIMITE_MAXIMO))


def test_novato_provisorio_fica_fora_do_ranking(repo: Repositorio) -> None:
    apelidos = [linha["apelido"] for linha in ranking.ver_ranking(repo, 50)["jogadores"]]
    assert "luma_dev" not in apelidos


def test_posicao_de_um_jogador_ranqueado(repo: Repositorio) -> None:
    resposta = ranking.posicao_do_jogador(repo, "voltz_br")
    assert resposta["encontrado"]
    assert resposta["posicao"] == 3
    assert resposta["rating"] == 1482
    assert not resposta["provisorio"]
    assert resposta["partidas_para_entrar"] == 0
    assert "3º" in resposta["mensagem"]


def test_posicao_de_um_provisorio_diz_quantas_partidas_faltam(repo: Repositorio) -> None:
    resposta = ranking.posicao_do_jogador(repo, "luma_dev")
    assert resposta["encontrado"]
    assert resposta["posicao"] is None
    assert resposta["provisorio"]
    assert resposta["partidas"] == 2
    assert resposta["partidas_para_entrar"] == 3
    assert "3 partidas" in resposta["mensagem"]


def test_apelido_sem_diferenciar_maiusculas_nem_espacos(repo: Repositorio) -> None:
    resposta = ranking.posicao_do_jogador(repo, "  VOLTZ_BR ")
    assert resposta["encontrado"]
    assert resposta["apelido"] == "voltz_br"


def test_apelido_inexistente_responde_sem_erro(repo: Repositorio) -> None:
    resposta = ranking.posicao_do_jogador(repo, "ninguem")
    assert not resposta["encontrado"]
    assert resposta["posicao"] is None
    assert "ninguem" in resposta["mensagem"]


def test_respostas_nao_trazem_email(repo: Repositorio) -> None:
    textos = str(ranking.ver_ranking(repo, 50)) + str(ranking.posicao_do_jogador(repo, "voltz_br"))
    assert "@" not in textos


def _pelo_cliente(nome: str, argumentos: dict[str, Any]) -> tuple[list[Any], Any]:
    servidor = ranking.criar_servidor(RepositorioMemoria())

    async def conversar() -> tuple[list[Any], Any]:
        async with Client(servidor) as cliente:
            ferramentas = (await cliente.list_tools()).tools
            resultado = await cliente.call_tool(nome, argumentos)
            return ferramentas, resultado

    return anyio.run(conversar)


def test_servidor_lista_as_duas_ferramentas_so_de_leitura() -> None:
    ferramentas, _ = _pelo_cliente("ver_ranking", {})
    assert {f.name for f in ferramentas} == {"ver_ranking", "posicao_do_jogador"}
    for ferramenta in ferramentas:
        assert ferramenta.annotations is not None
        assert ferramenta.annotations.read_only_hint
        assert ferramenta.description


def test_servidor_devolve_resultado_estruturado() -> None:
    _, resultado = _pelo_cliente("ver_ranking", {"limite": 2})
    assert not resultado.is_error
    assert [linha["apelido"] for linha in resultado.structured_content["jogadores"]] == ["ninacircuit", "lia.ohm"]

    _, resultado = _pelo_cliente("posicao_do_jogador", {"apelido": "luma_dev"})
    assert resultado.structured_content["partidas_para_entrar"] == 3
