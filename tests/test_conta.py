from typing import Any

import pytest

from circuitcrash.domain import conta
from circuitcrash.domain.conta import ErroLogin, Identidade, conferir_identidade, sugerir_apelido

CLIENTE = "cliente-123.apps.googleusercontent.com"
AGORA = 1_790_000_000


def info(**mudancas: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "iss": "https://accounts.google.com",
        "aud": CLIENTE,
        "exp": AGORA + 3600,
        "iat": AGORA,
        "nonce": "n-1",
        "sub": "1098765",
        "email": "Ana.Souza@gmail.com",
        "email_verified": True,
        "name": "Ana Souza",
    }
    base.update(mudancas)
    return {k: v for k, v in base.items() if v is not None}


# ---------- conferir a identidade ----------


def test_identidade_boa() -> None:
    assert conferir_identidade(info(), CLIENTE, "n-1", AGORA) == Identidade(
        "1098765", "ana.souza@gmail.com", "Ana Souza"
    )


def test_emissor_sem_https_tambem_vale() -> None:
    assert conferir_identidade(info(iss="accounts.google.com"), CLIENTE, "n-1", AGORA).sub == "1098765"


def test_sem_nome_fica_vazio() -> None:
    assert conferir_identidade(info(name=None), CLIENTE, "n-1", AGORA).nome == ""


@pytest.mark.parametrize(
    "ruim",
    [
        info(iss="https://evil.example.com"),
        info(aud="outro-cliente"),
        info(exp=AGORA),
        info(exp=AGORA - 10),
        info(nonce="outro"),
        info(nonce=None),
        info(email_verified=False),
        info(email_verified="false"),
        info(email_verified=None),
        info(sub=None),
        info(sub=""),
        info(email=None),
    ],
)
def test_identidade_recusada(ruim: dict[str, Any]) -> None:
    with pytest.raises(ErroLogin):
        conferir_identidade(ruim, CLIENTE, "n-1", AGORA)


def test_aud_em_lista_com_o_cliente_vale() -> None:
    assert conferir_identidade(info(aud=[CLIENTE]), CLIENTE, "n-1", AGORA).sub == "1098765"


def test_email_verified_em_texto_true_vale() -> None:
    assert conferir_identidade(info(email_verified="true"), CLIENTE, "n-1", AGORA).sub == "1098765"


def test_mensagem_do_erro_e_para_pessoas() -> None:
    with pytest.raises(ErroLogin, match="e-mail"):
        conferir_identidade(info(email_verified=False), CLIENTE, "n-1", AGORA)


# ---------- apelido ----------


@pytest.mark.parametrize(
    ("nome", "email", "esperado"),
    [
        ("Ana Souza", "ana@gmail.com", "ana_souza"),
        ("João Conceição", "j@gmail.com", "joao_conceicao"),
        ("  Zé   do Ó  ", "z@gmail.com", "ze_do_o"),
        ("Maria!! (UFPA) #1", "m@gmail.com", "maria_ufpa_1"),
        ("", "carlos.lima-99@gmail.com", "carlos.lima-99"),
        ("Um Nome Muito Comprido Demais Para Caber", "x@gmail.com", "um_nome_muito_compri"),
        ("李小龙", "", "jogador"),
        ("", "", "jogador"),
    ],
)
def test_sugerir_apelido(nome: str, email: str, esperado: str) -> None:
    assert sugerir_apelido(nome, email, set()) == esperado


def test_apelido_repetido_ganha_numero() -> None:
    assert sugerir_apelido("Ana Souza", "", {"ana_souza"}) == "ana_souza2"
    assert sugerir_apelido("Ana Souza", "", {"ana_souza", "ana_souza2"}) == "ana_souza3"


def test_apelido_repetido_sem_diferenciar_maiusculas() -> None:
    assert sugerir_apelido("Voltz BR", "", {"VOLTZ_BR"}) == "voltz_br2"


def test_apelido_comprido_repetido_continua_em_20() -> None:
    longo = "um_nome_muito_compri"
    novo = sugerir_apelido("Um Nome Muito Comprido Demais", "", {longo})
    assert novo == "um_nome_muito_compr2"
    assert len(novo) <= conta.TAMANHO_APELIDO
