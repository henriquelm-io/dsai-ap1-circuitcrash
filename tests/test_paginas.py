from collections.abc import Iterator
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from circuitcrash.app import criar_app
from conftest import criar_repo_sql


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
