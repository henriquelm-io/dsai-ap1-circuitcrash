"""Peças usadas pelos três servidores MCP."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from circuitcrash.dados.config import carregar_env, url_do_banco
from circuitcrash.dados.fabrica import criar_repositorio
from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.domain.modelos import Jogador

# Nenhuma ferramenta muda dados: só consulta o banco do próprio projeto.
SO_LEITURA = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)


def repositorio_do_ambiente() -> Repositorio:
    """O mesmo banco do site: DATABASE_URL do .env, ou dados de exemplo em memória."""
    carregar_env()
    return criar_repositorio(url_do_banco())


def buscar_por_apelido(repo: Repositorio, apelido: str) -> Jogador | None:
    """Sem diferenciar maiúsculas e ignorando espaços nas pontas."""
    procurado = apelido.strip().casefold()
    return next((j for j in repo.listar_jogadores() if j.apelido.casefold() == procurado), None)
