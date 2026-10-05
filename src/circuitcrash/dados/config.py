"""Configuração do banco de dados.

O .env só é lido pelos pontos de entrada (servidor, carga e Alembic), nunca ao
importar o app, para que os testes não dependam da máquina de quem os roda.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def carregar_env(arquivo: str | Path = ".env") -> None:
    """Lê o .env, se existir, sem sobrescrever variáveis já definidas."""
    if Path(arquivo).is_file():
        load_dotenv(arquivo, override=False)


def normalizar_url(url: str) -> str:
    """postgresql:// usaria o psycopg2; o projeto usa o psycopg 3."""
    for prefixo in ("postgresql://", "postgres://"):
        if url.startswith(prefixo):
            return "postgresql+psycopg://" + url[len(prefixo) :]
    return url


def url_do_banco() -> str | None:
    """URL de DATABASE_URL, ou None quando vazia (usa os dados em memória)."""
    url = os.environ.get("DATABASE_URL", "").strip()
    return normalizar_url(url) if url else None
