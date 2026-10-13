"""Regras da loja de avatares. Recebe o repositório pronto; não sabe se há banco."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.domain.modelos import Avatar, Jogador


@dataclass(frozen=True)
class Resultado:
    ok: bool
    mensagem: str


class Situacao(StrEnum):
    """Como um avatar aparece para o jogador na loja (os valores são os do template loja.html)."""

    EM_USO = "em_uso"
    POSSUI = "possui"
    EXCLUSIVO = "exclusivo"
    COMPRAR = "comprar"
    FALTA = "falta"


def situacao(avatar: Avatar, jogador: Jogador, inventario: set[str]) -> Situacao:
    """A mesma para a tela /loja e para o servidor MCP (spec 012)."""
    if avatar.id == jogador.avatar_id:
        return Situacao.EM_USO
    if avatar.id in inventario:
        return Situacao.POSSUI
    if avatar.preco is None:
        return Situacao.EXCLUSIVO
    if avatar.preco <= jogador.fagulhas:
        return Situacao.COMPRAR
    return Situacao.FALTA


def faltam(avatar: Avatar, jogador: Jogador) -> int:
    """Fagulhas que faltam para comprar; 0 se o saldo cobre ou se o avatar não é vendido."""
    return max(0, (avatar.preco or 0) - jogador.fagulhas)


def comprar(repo: Repositorio, jogador_id: str, avatar_id: str) -> Resultado:
    jogador = repo.obter_jogador(jogador_id)
    avatar = repo.obter_avatar(avatar_id)
    if jogador is None or avatar is None:
        return Resultado(False, "Avatar ou jogador não encontrado.")
    if avatar.preco is None:
        return Resultado(False, f"{avatar.nome} é exclusivo de campeonato e não pode ser comprado.")
    if avatar_id in repo.inventario(jogador_id):
        return Resultado(False, f"Você já tem o {avatar.nome}.")
    if jogador.fagulhas < avatar.preco:
        falta = avatar.preco - jogador.fagulhas
        return Resultado(False, f"Faltam {falta} Fagulhas para o {avatar.nome}.")

    jogador.fagulhas -= avatar.preco
    repo.adicionar_ao_inventario(jogador_id, avatar_id)
    if jogador.avatar_id is None:
        jogador.avatar_id = avatar_id
    repo.salvar_jogador(jogador)
    return Resultado(True, f"{avatar.nome} é seu! Ele já está no seu inventário.")


def equipar(repo: Repositorio, jogador_id: str, avatar_id: str) -> Resultado:
    jogador = repo.obter_jogador(jogador_id)
    avatar = repo.obter_avatar(avatar_id)
    if jogador is None or avatar is None:
        return Resultado(False, "Avatar ou jogador não encontrado.")
    if avatar_id not in repo.inventario(jogador_id):
        return Resultado(False, f"Você ainda não tem o {avatar.nome}.")
    jogador.avatar_id = avatar_id
    repo.salvar_jogador(jogador)
    return Resultado(True, f"Agora você está usando o {avatar.nome}.")
