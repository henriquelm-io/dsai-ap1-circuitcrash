import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from starlette.testclient import TestClient

from circuitcrash.app import criar_app
from circuitcrash.dados.sql import RepositorioSQL
from conftest import HOJE, criar_repo_sql, url_sqlite


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(criar_app())


@pytest.mark.parametrize("rota", ["/", "/partida", "/perfil", "/loja", "/loja?raridade=raro", "/ranking", "/regras"])
def test_paginas_abrem(cliente: TestClient, rota: str) -> None:
    resposta = cliente.get(rota)
    assert resposta.status_code == 200
    assert "CIRCUIT" in resposta.text


def test_health(cliente: TestClient) -> None:
    assert cliente.get("/health").json() == {"status": "ok"}


def test_jogada_via_htmx_devolve_so_o_jogo(cliente: TestClient) -> None:
    cliente.get("/partida")
    resposta = cliente.post("/partida/jogar", data={"linha": "2", "coluna": "3"}, headers={"HX-Request": "true"})
    assert resposta.status_code == 200
    assert resposta.text.lstrip().startswith('<div id="jogo"') or 'id="jogo"' in resposta.text[:400]
    assert "<html" not in resposta.text
    assert "capturou Bateria" in resposta.text


def test_jogada_sem_htmx_redireciona(cliente: TestClient) -> None:
    resposta = cliente.post("/partida/passar", follow_redirects=False)
    assert resposta.status_code == 303


def test_trocar_para_novato_mostra_sem_avatar(cliente: TestClient) -> None:
    cliente.post("/jogador", data={"jogador_id": "novato"})
    resposta = cliente.get("/perfil")
    assert "Sem avatar ainda" in resposta.text


def test_comprar_avatar_mostra_aviso(cliente: TestClient) -> None:
    resposta = cliente.post("/loja/comprar", data={"avatar_id": "onda"})
    assert resposta.status_code == 200
    assert "Onda é seu" in resposta.text


# ---------- com o banco (spec 002) ----------


@pytest.fixture
def cliente_sql(tmp_path: Path) -> Iterator[TestClient]:
    repo = criar_repo_sql(tmp_path)
    yield TestClient(criar_app(repo))
    repo.fechar()


@pytest.mark.parametrize("rota", ["/", "/perfil", "/loja", "/loja?raridade=raro", "/ranking", "/regras"])
def test_paginas_com_banco_iguais_as_da_memoria(cliente: TestClient, cliente_sql: TestClient, rota: str) -> None:
    resposta = cliente_sql.get(rota)
    assert resposta.status_code == 200
    assert resposta.text == cliente.get(rota).text


def test_paginas_do_novato_com_banco(cliente: TestClient, cliente_sql: TestClient) -> None:
    for c in (cliente, cliente_sql):
        c.post("/jogador", data={"jogador_id": "novato"})
    assert cliente_sql.get("/perfil").text == cliente.get("/perfil").text


def test_compra_com_banco_aparece_no_perfil(cliente_sql: TestClient) -> None:
    resposta = cliente_sql.post("/loja/comprar", data={"avatar_id": "onda"})
    assert "Onda é seu" in resposta.text
    assert "Onda" in cliente_sql.get("/perfil").text


# ---------- partida gravada no fim (spec 006) ----------


def _jogar_ate_o_fim(cliente: TestClient, htmx: bool = False) -> Any:
    """A partida de demonstração começa na rodada 6; passar 7 vezes a encerra."""
    cliente.get("/partida")
    for _ in range(6):
        cliente.post("/partida/passar")
    headers = {"HX-Request": "true"} if htmx else {}
    return cliente.post("/partida/passar", headers=headers, follow_redirects=not htmx)


def _fagulhas_no_cabecalho(html: str) -> int:
    achado = re.search(r"Fagulhas: </span>(\d+)", html)
    assert achado is not None
    return int(achado.group(1))


def test_fim_de_partida_grava_e_mostra_o_resultado(cliente: TestClient) -> None:
    # Passando sempre, "Você" fica em 3º com 4 pontos: +15 Fagulhas e rating 1482 -> 1466.
    resposta = _jogar_ate_o_fim(cliente)
    assert "Seu resultado" in resposta.text
    assert "+15 Fagulhas" in resposta.text
    assert "1482 → 1466" in resposta.text
    assert _fagulhas_no_cabecalho(resposta.text) == 320 + 15


def test_fim_de_partida_grava_uma_vez_so(cliente: TestClient) -> None:
    _jogar_ate_o_fim(cliente)
    cliente.post("/partida/passar")
    resposta = cliente.get("/partida")
    assert _fagulhas_no_cabecalho(resposta.text) == 335
    perfil = cliente.get("/perfil").text
    assert perfil.count("+15</td>") == 2  # a partida nova e a de exemplo de "hoje"


def test_fim_de_partida_via_htmx_pede_para_recarregar(cliente: TestClient) -> None:
    resposta = _jogar_ate_o_fim(cliente, htmx=True)
    assert resposta.headers.get("HX-Refresh") == "true"
    assert "Seu resultado" in resposta.text
    seguinte = cliente.post("/partida/passar", headers={"HX-Request": "true"})
    assert "HX-Refresh" not in seguinte.headers


def test_partida_gravada_aparece_no_perfil(cliente: TestClient) -> None:
    _jogar_ate_o_fim(cliente)
    perfil = cliente.get("/perfil").text
    corpo = perfil[perfil.index("<tbody>", perfil.index("Partidas recentes")) :]
    primeira = corpo[: corpo.index("</tr>")]
    assert "3º" in primeira and "-16" in primeira and "+15" in primeira and "hoje" in primeira


def test_jogar_de_novo_grava_outra_partida(cliente: TestClient) -> None:
    _jogar_ate_o_fim(cliente)
    cliente.post("/partida/nova")
    resposta = _jogar_ate_o_fim(cliente)
    assert _fagulhas_no_cabecalho(resposta.text) == 320 + 15 + 15


def test_partida_nao_terminada_nao_grava(cliente: TestClient) -> None:
    cliente.get("/partida")
    cliente.post("/partida/passar")
    resposta = cliente.get("/partida")
    assert "Seu resultado" not in resposta.text
    assert _fagulhas_no_cabecalho(resposta.text) == 320


def test_partida_do_novato_usa_k_provisorio(cliente: TestClient) -> None:
    cliente.post("/jogador", data={"jogador_id": "novato"})
    resposta = _jogar_ate_o_fim(cliente)
    # Rating igual ao dos adversários: 3º lugar = 48/3 * (0 + 0 + 1 - 1.5) = -8.
    assert "1200 → 1192" in resposta.text
    assert _fagulhas_no_cabecalho(resposta.text) == 60 + 15


def test_fim_de_partida_com_banco_persiste(cliente_sql: TestClient, tmp_path: Path) -> None:
    _jogar_ate_o_fim(cliente_sql)
    reaberto = RepositorioSQL(url_sqlite(tmp_path), hoje=lambda: HOJE)
    veterano = reaberto.obter_jogador("veterano")
    assert veterano is not None
    assert (veterano.fagulhas, veterano.rating, veterano.partidas) == (335, 1466, 49)
    assert reaberto.partidas_recentes("veterano")[0].quando == "hoje"
    reaberto.fechar()
