"""Consulta da loja de avatares pelo servidor MCP (spec 012).

Só leitura: não compra, não equipa e não grava nada. Preço e raridade vêm de
domain/modelos.py, e a situação de cada avatar de domain/loja.py, a mesma regra
da tela /loja.
"""

from __future__ import annotations

from typing import TypedDict

from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.domain import loja
from circuitcrash.domain.modelos import Avatar
from circuitcrash.mcps.comum import buscar_por_apelido


class AvatarResumo(TypedDict):
    id: str
    nome: str
    raridade: str


class ItemCatalogo(TypedDict):
    id: str
    nome: str
    raridade: str
    preco: int | None
    vendavel: bool
    situacao: str
    possui: bool
    equipado: bool
    pode_comprar: bool
    faltam: int


class RespostaLoja(TypedDict):
    encontrado: bool
    apelido: str
    fagulhas: int
    avatar_equipado: AvatarResumo | None
    possuidos: list[AvatarResumo]
    catalogo: list[ItemCatalogo]
    compraveis: int
    mensagem: str


def _resumo(avatar: Avatar) -> AvatarResumo:
    return {"id": avatar.id, "nome": avatar.nome, "raridade": avatar.raridade.rotulo}


def consultar_loja(repo: Repositorio, apelido: str) -> RespostaLoja:
    jogador = buscar_por_apelido(repo, apelido)
    if jogador is None:
        return {
            "encontrado": False,
            "apelido": apelido.strip(),
            "fagulhas": 0,
            "avatar_equipado": None,
            "possuidos": [],
            "catalogo": [],
            "compraveis": 0,
            "mensagem": f"Nenhum jogador com o apelido {apelido.strip()!r}.",
        }

    avatares = repo.listar_avatares()
    meus = repo.inventario(jogador.id)
    catalogo: list[ItemCatalogo] = []
    for avatar in avatares:
        situacao = loja.situacao(avatar, jogador, meus)
        catalogo.append(
            {
                "id": avatar.id,
                "nome": avatar.nome,
                "raridade": avatar.raridade.rotulo,
                "preco": avatar.preco,
                "vendavel": avatar.preco is not None,
                "situacao": situacao.value,
                "possui": avatar.id in meus,
                "equipado": situacao is loja.Situacao.EM_USO,
                "pode_comprar": situacao is loja.Situacao.COMPRAR,
                "faltam": loja.faltam(avatar, jogador) if situacao is loja.Situacao.FALTA else 0,
            }
        )
    equipado = next((a for a in avatares if a.id == jogador.avatar_id), None)
    compraveis = [a.nome for a, item in zip(avatares, catalogo, strict=True) if item["pode_comprar"]]

    usa = f"usa o {equipado.nome}" if equipado else "ainda não tem avatar equipado"
    if compraveis:
        oferta = f"Pode comprar agora: {', '.join(compraveis)}."
    else:
        a_venda = [a.preco for a in avatares if a.preco is not None and a.id not in meus]
        oferta = "Nenhum avatar cabe no saldo"
        oferta += f"; o mais barato à venda custa {min(a_venda)}." if a_venda else "."
    return {
        "encontrado": True,
        "apelido": jogador.apelido,
        "fagulhas": jogador.fagulhas,
        "avatar_equipado": _resumo(equipado) if equipado else None,
        "possuidos": [_resumo(a) for a in avatares if a.id in meus],
        "catalogo": catalogo,
        "compraveis": len(compraveis),
        "mensagem": f"{jogador.apelido} tem {jogador.fagulhas} Fagulhas e {usa}. {oferta}",
    }
