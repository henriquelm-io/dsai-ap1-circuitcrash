"""Regras do login com a conta Google (spec 008).

Python puro: as informações do id_token, o client_id, o nonce e o horário
atual chegam como parâmetros. A conversa com o Google fica em circuitcrash.login.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

EMISSORES_GOOGLE = ("accounts.google.com", "https://accounts.google.com")
TAMANHO_APELIDO = 20
APELIDO_PADRAO = "jogador"


class ErroLogin(Exception):
    """Falha no login; a mensagem é mostrada no aviso da tela."""


@dataclass(frozen=True)
class Identidade:
    sub: str
    email: str
    nome: str


def _verdadeiro(valor: Any) -> bool:
    return valor is True or (isinstance(valor, str) and valor.lower() == "true")


def conferir_identidade(info: Mapping[str, Any], client_id: str, nonce: str, agora: int) -> Identidade:
    """Confere as informações do id_token recebido do Google e devolve a identidade.

    `agora` é o horário em segundos desde 1970 (como o `exp` do token).
    """
    if info.get("iss") not in EMISSORES_GOOGLE:
        raise ErroLogin("A resposta não veio do Google.")
    aud = info.get("aud")
    destinatarios = aud if isinstance(aud, list) else [aud]
    if client_id not in destinatarios:
        raise ErroLogin("A resposta do Google não era para o CircuitCrash.")
    exp = info.get("exp")
    if not isinstance(exp, int | float) or exp <= agora:
        raise ErroLogin("O login expirou. Tente de novo.")
    if not nonce or info.get("nonce") != nonce:
        raise ErroLogin("Esta resposta não pertence à sua tentativa de login. Tente de novo.")
    sub = info.get("sub")
    email = info.get("email")
    if not isinstance(sub, str) or not sub or not isinstance(email, str) or not email:
        raise ErroLogin("O Google não informou a conta.")
    if not _verdadeiro(info.get("email_verified")):
        raise ErroLogin("Confirme o seu e-mail na conta Google antes de entrar.")
    nome = info.get("name")
    return Identidade(sub, email.strip().lower(), nome.strip() if isinstance(nome, str) else "")


def _limpar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    com_sublinhado = re.sub(r"\s+", "_", sem_acento.strip().lower())
    so_validos = re.sub(r"[^a-z0-9._-]+", "_", com_sublinhado)
    return re.sub(r"_+", "_", so_validos).strip("_")[:TAMANHO_APELIDO].rstrip("_")


def sugerir_apelido(nome: str, email: str, ocupados: set[str]) -> str:
    """Apelido a partir do nome do Google (ou do e-mail), sem repetir os ocupados."""
    base = _limpar(nome) or _limpar(email.split("@")[0]) or APELIDO_PADRAO
    ocupados_min = {a.lower() for a in ocupados}
    if base not in ocupados_min:
        return base
    numero = 2
    while True:
        sufixo = str(numero)
        candidato = base[: TAMANHO_APELIDO - len(sufixo)] + sufixo
        if candidato not in ocupados_min:
            return candidato
        numero += 1
