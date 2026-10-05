"""Rotas do login Google (spec 008), com um Google falso: nenhum teste acessa a rede."""

import base64
import json
import time
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from starlette.testclient import TestClient

from circuitcrash.app import criar_app
from circuitcrash.dados.memoria import RepositorioMemoria
from circuitcrash.domain.conta import ErroLogin
from circuitcrash.login.google import (
    ConfigGoogle,
    desafio_pkce,
    ler_id_token,
)

CONFIG = ConfigGoogle("cliente-123.apps.googleusercontent.com", "chave-de-teste", None)


class GoogleFalso:
    """Faz o papel do endpoint de token: devolve as informações do id_token."""

    def __init__(self) -> None:
        self.info: dict[str, Any] = {}
        self.chamadas: list[tuple[str, str, str]] = []
        self.erro: ErroLogin | None = None

    def __call__(self, config: ConfigGoogle, code: str, verificador: str, redirect_uri: str) -> dict[str, Any]:
        self.chamadas.append((code, verificador, redirect_uri))
        if self.erro:
            raise self.erro
        return self.info


@pytest.fixture
def google() -> GoogleFalso:
    return GoogleFalso()


@pytest.fixture
def cliente(google: GoogleFalso) -> TestClient:
    return TestClient(criar_app(RepositorioMemoria(), google_config=CONFIG, trocar_codigo=google))


def iniciar(cliente: TestClient) -> dict[str, str]:
    resposta = cliente.get("/entrar", follow_redirects=False)
    assert resposta.status_code == 303
    url = urlparse(resposta.headers["location"])
    assert f"{url.scheme}://{url.netloc}{url.path}" == "https://accounts.google.com/o/oauth2/v2/auth"
    return {k: v[0] for k, v in parse_qs(url.query).items()}


def info_boa(nonce_da_tentativa: str, **mudancas: Any) -> dict[str, Any]:
    info: dict[str, Any] = {
        "iss": "https://accounts.google.com",
        "aud": CONFIG.client_id,
        "exp": int(time.time()) + 3600,
        "nonce": nonce_da_tentativa,
        "sub": "1098765",
        "email": "ana.souza@gmail.com",
        "email_verified": True,
        "name": "Ana Souza",
    }
    info.update(mudancas)
    return info


def entrar(cliente: TestClient, google: GoogleFalso, **mudancas: Any) -> Any:
    parametros = iniciar(cliente)
    google.info = info_boa(parametros["nonce"], **mudancas)
    return cliente.get(f"/auth/google/retorno?code=codigo-1&state={parametros['state']}")


# ---------- sem configuração ----------


def test_sem_configuracao_nao_mostra_o_botao(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    cliente = TestClient(criar_app(RepositorioMemoria()))
    assert "Entrar com Google" not in cliente.get("/").text
    resposta = cliente.get("/entrar")
    assert resposta.url.path == "/"
    assert "não está configurado" in resposta.text


def test_configuracao_vem_do_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", " id ")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "segredo")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "https://exemplo.com/auth/google/retorno")
    assert ConfigGoogle.do_ambiente() == ConfigGoogle("id", "segredo", "https://exemplo.com/auth/google/retorno")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "")
    assert ConfigGoogle.do_ambiente() is None


# ---------- ida ao Google ----------


def test_botao_aparece_com_configuracao(cliente: TestClient) -> None:
    assert "Entrar com Google" in cliente.get("/").text


def test_entrar_redireciona_ao_google_com_state_nonce_e_pkce(cliente: TestClient) -> None:
    parametros = iniciar(cliente)
    assert parametros["client_id"] == CONFIG.client_id
    assert parametros["redirect_uri"] == "http://testserver/auth/google/retorno"
    assert parametros["response_type"] == "code"
    assert parametros["scope"] == "openid email profile"
    assert parametros["code_challenge_method"] == "S256"
    assert len(parametros["state"]) >= 32 and len(parametros["nonce"]) >= 32
    assert len(parametros["code_challenge"]) == 43
    assert "client_secret" not in parametros


def test_cada_tentativa_tem_codigos_novos(cliente: TestClient) -> None:
    assert iniciar(cliente)["state"] != iniciar(cliente)["state"]


def test_redirect_uri_fixo_vence_o_da_requisicao(google: GoogleFalso) -> None:
    fixo = ConfigGoogle("id", "segredo", "https://circuitcrash.onrender.com/auth/google/retorno")
    cliente = TestClient(criar_app(RepositorioMemoria(), google_config=fixo, trocar_codigo=google))
    assert iniciar(cliente)["redirect_uri"] == fixo.redirect_uri


# ---------- volta do Google ----------


def test_primeira_entrada_cria_o_jogador_e_abre_o_perfil(cliente: TestClient, google: GoogleFalso) -> None:
    resposta = entrar(cliente, google)
    assert resposta.url.path == "/perfil"
    assert "Olá, ana_souza!" in resposta.text
    assert "ana_souza" in resposta.text
    assert "Sair" in resposta.text
    assert 'name="jogador_id"' not in resposta.text  # sem o seletor Demo como
    code, verificador, redirect_uri = google.chamadas[0]
    assert code == "codigo-1"
    assert redirect_uri == "http://testserver/auth/google/retorno"
    assert len(verificador) >= 43


def test_verificador_bate_com_o_desafio(cliente: TestClient, google: GoogleFalso) -> None:
    parametros = iniciar(cliente)
    google.info = info_boa(parametros["nonce"])
    cliente.get(f"/auth/google/retorno?code=c&state={parametros['state']}")
    assert desafio_pkce(google.chamadas[0][1]) == parametros["code_challenge"]


def test_jogador_novo_comeca_zerado(cliente: TestClient, google: GoogleFalso) -> None:
    entrar(cliente, google)
    loja = cliente.get("/loja").text
    assert "Fagulhas: </span>0" in loja


def test_segunda_entrada_volta_ao_mesmo_jogador(cliente: TestClient, google: GoogleFalso) -> None:
    entrar(cliente, google)
    cliente.post("/sair")
    resposta = entrar(cliente, google)
    assert "Olá, ana_souza!" in resposta.text
    assert "ana_souza2" not in resposta.text


def test_state_errado_nao_entra(cliente: TestClient, google: GoogleFalso) -> None:
    parametros = iniciar(cliente)
    google.info = info_boa(parametros["nonce"])
    resposta = cliente.get("/auth/google/retorno?code=c&state=outro")
    assert resposta.url.path == "/"
    assert "tentativa de login" in resposta.text
    assert google.chamadas == []
    assert "voltz_br" in resposta.text


def test_state_com_acento_nao_quebra(cliente: TestClient, google: GoogleFalso) -> None:
    iniciar(cliente)
    resposta = cliente.get("/auth/google/retorno?code=c&state=%C3%A7%C3%A3o")
    assert resposta.status_code == 200
    assert resposta.url.path == "/"
    assert google.chamadas == []


def test_retorno_sem_tentativa_nao_entra(cliente: TestClient, google: GoogleFalso) -> None:
    resposta = cliente.get("/auth/google/retorno?code=c&state=qualquer")
    assert resposta.url.path == "/"
    assert google.chamadas == []


def test_retorno_repetido_nao_entra_de_novo(cliente: TestClient, google: GoogleFalso) -> None:
    parametros = iniciar(cliente)
    google.info = info_boa(parametros["nonce"])
    url = f"/auth/google/retorno?code=c&state={parametros['state']}"
    cliente.get(url)
    cliente.post("/sair")
    resposta = cliente.get(url)
    assert resposta.url.path == "/"
    assert len(google.chamadas) == 1


def test_cancelar_no_google(cliente: TestClient, google: GoogleFalso) -> None:
    parametros = iniciar(cliente)
    resposta = cliente.get(f"/auth/google/retorno?error=access_denied&state={parametros['state']}")
    assert resposta.url.path == "/"
    assert "Login cancelado" in resposta.text
    assert google.chamadas == []


def test_nonce_errado_nao_entra(cliente: TestClient, google: GoogleFalso) -> None:
    resposta = entrar(cliente, google, nonce="outro")
    assert resposta.url.path == "/"
    assert "não pertence à sua tentativa" in resposta.text
    assert "Sair" not in resposta.text


def test_email_nao_confirmado_nao_entra(cliente: TestClient, google: GoogleFalso) -> None:
    resposta = entrar(cliente, google, email_verified=False)
    assert "Confirme o seu e-mail" in resposta.text


def test_falha_ao_falar_com_o_google(cliente: TestClient, google: GoogleFalso) -> None:
    google.erro = ErroLogin("Não foi possível falar com o Google. Tente de novo.")
    resposta = entrar(cliente, google)
    assert resposta.url.path == "/"
    assert "Não foi possível falar com o Google" in resposta.text


# ---------- sair e Demo como ----------


def test_sair_volta_ao_perfil_padrao(cliente: TestClient, google: GoogleFalso) -> None:
    entrar(cliente, google)
    resposta = cliente.post("/sair")
    assert resposta.url.path == "/"
    assert "Você saiu." in resposta.text
    perfil = cliente.get("/perfil").text
    assert "voltz_br" in perfil and "Entrar com Google" in perfil


def test_demo_como_so_aceita_perfis_de_demonstracao(cliente: TestClient) -> None:
    cliente.post("/jogador", data={"jogador_id": "nina"})
    assert "ninacircuit" not in cliente.get("/perfil").text
    cliente.post("/jogador", data={"jogador_id": "novato"})
    assert "luma_dev" in cliente.get("/perfil").text


def test_demo_como_nao_entra_na_conta_google_de_outra_pessoa(cliente: TestClient, google: GoogleFalso) -> None:
    entrar(cliente, google)
    outro = TestClient(cliente.app)
    for jogador_id in ("g-", "g-" + "0" * 12):
        outro.post("/jogador", data={"jogador_id": jogador_id})
    assert "ana_souza" not in outro.get("/perfil").text


def test_entrar_com_google_comeca_partida_nova(cliente: TestClient, google: GoogleFalso) -> None:
    cliente.get("/partida")
    cliente.post("/partida/passar")
    entrar(cliente, google)
    assert "Rodada 6 de 12" in cliente.get("/partida").text


# ---------- id_token ----------


def _token(info: dict[str, Any]) -> str:
    def parte(dados: dict[str, Any]) -> str:
        return base64.urlsafe_b64encode(json.dumps(dados).encode()).rstrip(b"=").decode()

    return f"{parte({'alg': 'RS256'})}.{parte(info)}.assinatura"


def test_ler_id_token() -> None:
    assert ler_id_token(_token({"sub": "1", "name": "Ana Souza"})) == {"sub": "1", "name": "Ana Souza"}


@pytest.mark.parametrize("ruim", ["", "a.b", "a.!!!.c", "a.b.c.d", "a.W10.c"])
def test_ler_id_token_invalido(ruim: str) -> None:
    with pytest.raises(ErroLogin):
        ler_id_token(ruim)
