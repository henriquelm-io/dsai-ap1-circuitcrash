"""Conversa com o Google no login (spec 008): OpenID Connect com state, nonce e PKCE.

Só a biblioteca padrão. O id_token vem direto do endpoint de token do Google, por
HTTPS e numa chamada do servidor, então a assinatura não precisa ser conferida
(OpenID Connect Core, 3.1.3.7, item 6). Quem confere o conteúdo é
circuitcrash.domain.conta.conferir_identidade.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any

from circuitcrash.domain.conta import ErroLogin

URL_AUTORIZACAO = "https://accounts.google.com/o/oauth2/v2/auth"
URL_TOKEN = "https://oauth2.googleapis.com/token"
ESCOPO = "openid email profile"


@dataclass(frozen=True)
class ConfigGoogle:
    client_id: str
    client_secret: str
    # Fixo quando o servidor fica atrás de um proxy (no Render ele enxerga http).
    redirect_uri: str | None = None

    @classmethod
    def do_ambiente(cls) -> ConfigGoogle | None:
        """Lê GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET e GOOGLE_REDIRECT_URI; None sem as duas primeiras."""
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
        if not client_id or not client_secret:
            return None
        return cls(client_id, client_secret, os.environ.get("GOOGLE_REDIRECT_URI", "").strip() or None)


@dataclass(frozen=True)
class Tentativa:
    """Códigos de uma tentativa de login, guardados na sessão do navegador."""

    state: str
    nonce: str
    verificador: str

    def para_sessao(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def da_sessao(cls, dados: Any) -> Tentativa | None:
        if not isinstance(dados, dict):
            return None
        try:
            return cls(str(dados["state"]), str(dados["nonce"]), str(dados["verificador"]))
        except KeyError:
            return None


# config, code, verificador PKCE, redirect_uri -> informações do id_token
TrocarCodigo = Callable[[ConfigGoogle, str, str, str], dict[str, Any]]


def nova_tentativa() -> Tentativa:
    return Tentativa(secrets.token_urlsafe(32), secrets.token_urlsafe(32), secrets.token_urlsafe(64))


def _base64url(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).rstrip(b"=").decode("ascii")


def desafio_pkce(verificador: str) -> str:
    return _base64url(hashlib.sha256(verificador.encode("ascii")).digest())


def url_de_autorizacao(config: ConfigGoogle, redirect_uri: str, tentativa: Tentativa) -> str:
    parametros = {
        "client_id": config.client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": ESCOPO,
        "state": tentativa.state,
        "nonce": tentativa.nonce,
        "code_challenge": desafio_pkce(tentativa.verificador),
        "code_challenge_method": "S256",
        "prompt": "select_account",
    }
    return f"{URL_AUTORIZACAO}?{urllib.parse.urlencode(parametros)}"


def ler_id_token(id_token: str) -> dict[str, Any]:
    """Informações (a parte do meio) de um id_token no formato JWT."""
    partes = id_token.split(".")
    if len(partes) != 3:
        raise ErroLogin("O Google devolveu uma resposta inválida.")
    meio = partes[1] + "=" * (-len(partes[1]) % 4)
    try:
        info = json.loads(base64.urlsafe_b64decode(meio))
    except ValueError as erro:
        raise ErroLogin("O Google devolveu uma resposta inválida.") from erro
    if not isinstance(info, dict):
        raise ErroLogin("O Google devolveu uma resposta inválida.")
    return info


def trocar_codigo(config: ConfigGoogle, code: str, verificador: str, redirect_uri: str) -> dict[str, Any]:
    """Troca o código de autorização pelo id_token, direto com o Google."""
    corpo = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code_verifier": verificador,
        }
    ).encode("ascii")
    pedido = urllib.request.Request(
        URL_TOKEN,
        data=corpo,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(pedido, timeout=10) as resposta:  # URL fixa do Google
            dados = json.loads(resposta.read())
    except (urllib.error.URLError, TimeoutError, ValueError) as erro:
        raise ErroLogin("Não foi possível falar com o Google. Tente de novo.") from erro
    id_token = dados.get("id_token") if isinstance(dados, dict) else None
    if not isinstance(id_token, str):
        raise ErroLogin("O Google não devolveu a identidade da conta.")
    return ler_id_token(id_token)
