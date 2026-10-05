"""Escolhe a implementação do Repositorio pela URL do banco."""

from __future__ import annotations

from circuitcrash.dados.memoria import RepositorioMemoria
from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.dados.sql import RepositorioSQL


def criar_repositorio(url: str | None) -> Repositorio:
    """Sem URL, dados de exemplo em memória; com URL, o banco (SQLite ou PostgreSQL)."""
    if not url:
        return RepositorioMemoria()
    return RepositorioSQL(url)
