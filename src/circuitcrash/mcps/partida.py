"""Partida de demonstração jogada pelo servidor MCP (spec 011).

As regras são as de domain/tabuleiro.py, as mesmas da tela /partida. Aqui só
se guarda a partida em andamento, se traduz o estado em campos nomeados e se
grava o resultado uma vez, no fim.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import TypedDict

from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.domain import economia, tabuleiro
from circuitcrash.domain.modelos import ResultadoPartida
from circuitcrash.domain.tabuleiro import EstadoPartida, TipoCasa
from circuitcrash.mcps.comum import buscar_por_apelido

SEM_PARTIDA = "Nenhuma partida em andamento. Use iniciar_partida com o apelido de um jogador."


@dataclass
class Mesa:
    """A partida em andamento no servidor (uma por vez)."""

    estado: EstadoPartida | None = None
    jogador_id: str | None = None
    apelido: str = ""
    resultado: ResultadoPartida | None = None


class Placar(TypedDict):
    jogador: str
    pontos: int
    energizado: bool


class PecaDaMao(TypedDict):
    indice: int
    formato: str
    saidas: str


class CasaOcupada(TypedDict):
    linha: int
    coluna: int
    tipo: str
    saidas: str
    dono: str | None
    objetivo: str | None
    capturado_por: str | None


class Jogada(TypedDict):
    peca: int
    giros: int
    linha: int
    coluna: int
    saidas: str


class ResultadoGravado(TypedDict):
    colocacao: int
    pontos: int
    objetivos: int
    fagulhas: int
    limite_atingido: bool
    rating_antes: int
    variacao_rating: int
    rating_depois: int


class RespostaPartida(TypedDict):
    ativa: bool
    apelido: str
    aceita: bool
    mensagem: str
    rodada: int
    max_rodadas: int
    rodadas_restantes: int
    terminou: bool
    placar: list[Placar]
    mao: list[PecaDaMao]
    casas: list[CasaOcupada]
    jogadas_validas: list[Jogada]
    resultado: ResultadoGravado | None


def _nome(indice: int | None) -> str | None:
    return None if indice is None else tabuleiro.JOGADORES_DEMO[indice].nome


def _sem_partida(mensagem: str = SEM_PARTIDA) -> RespostaPartida:
    return {
        "ativa": False,
        "apelido": "",
        "aceita": False,
        "mensagem": mensagem,
        "rodada": 0,
        "max_rodadas": tabuleiro.MAX_RODADAS,
        "rodadas_restantes": 0,
        "terminou": False,
        "placar": [],
        "mao": [],
        "casas": [],
        "jogadas_validas": [],
        "resultado": None,
    }


def jogadas_validas(estado: EstadoPartida) -> list[Jogada]:
    """Cada peça da mão, em cada giro com saídas diferentes, nas casas vazias vizinhas do circuito.

    A validade vem do próprio domínio: a jogada é tentada numa cópia do estado.
    """
    if estado.terminou:
        return []
    circuito, _, _ = tabuleiro.circuito_do_jogador(estado, 0)
    candidatas = sorted(
        {
            (linha + dl, coluna + dc)
            for linha, coluna in circuito
            for dl, dc in tabuleiro.DIRECOES.values()
            if 0 <= linha + dl < tabuleiro.TAMANHO
            and 0 <= coluna + dc < tabuleiro.TAMANHO
            and estado.casa(linha + dl, coluna + dc).tipo is TipoCasa.VAZIA
        }
    )
    jogadas: list[Jogada] = []
    for indice, peca in enumerate(estado.mao):
        vistas: set[str] = set()
        for giros in range(4):
            saidas = tabuleiro.girar(peca.saidas, giros)
            if saidas in vistas:
                continue
            vistas.add(saidas)
            for linha, coluna in candidatas:
                teste = copy.deepcopy(estado)
                teste.selecionada = indice
                teste.mao[indice].saidas = saidas
                if tabuleiro.jogar_na_casa(teste, linha, coluna):
                    jogadas.append({"peca": indice, "giros": giros, "linha": linha, "coluna": coluna, "saidas": saidas})
    return jogadas


def _resposta(mesa: Mesa, aceita: bool, mensagem: str | None = None) -> RespostaPartida:
    estado = mesa.estado
    if estado is None:
        return _sem_partida()
    resultado: ResultadoGravado | None = None
    if mesa.resultado is not None:
        r = mesa.resultado
        resultado = {
            "colocacao": r.colocacao,
            "pontos": r.pontos,
            "objetivos": r.objetivos,
            "fagulhas": r.fagulhas,
            "limite_atingido": r.limite_atingido,
            "rating_antes": r.rating_antes,
            "variacao_rating": r.variacao_rating,
            "rating_depois": r.rating_depois,
        }
    return {
        "ativa": True,
        "apelido": mesa.apelido,
        "aceita": aceita,
        "mensagem": mensagem or estado.mensagem,
        "rodada": min(estado.rodada, tabuleiro.MAX_RODADAS),
        "max_rodadas": tabuleiro.MAX_RODADAS,
        "rodadas_restantes": max(0, tabuleiro.MAX_RODADAS - estado.rodada + 1),
        "terminou": estado.terminou,
        "placar": [
            {
                "jogador": j.nome,
                "pontos": estado.pontos[j.indice],
                "energizado": tabuleiro.circuito_do_jogador(estado, j.indice)[1],
            }
            for j in tabuleiro.JOGADORES_DEMO
        ],
        "mao": [{"indice": i, "formato": p.formato, "saidas": p.saidas} for i, p in enumerate(estado.mao)],
        "casas": [
            {
                "linha": linha,
                "coluna": coluna,
                "tipo": casa.tipo.value,
                "saidas": casa.saidas,
                "dono": _nome(casa.dono),
                "objetivo": casa.objetivo,
                "capturado_por": _nome(casa.capturado_por),
            }
            for linha, fileira in enumerate(estado.casas)
            for coluna, casa in enumerate(fileira)
            if casa.tipo is not TipoCasa.VAZIA
        ],
        "jogadas_validas": jogadas_validas(estado),
        "resultado": resultado,
    }


def _gravar_se_terminou(repo: Repositorio, mesa: Mesa) -> None:
    """Grava o resultado uma única vez, como a tela /partida."""
    if mesa.estado is None or not mesa.estado.terminou or mesa.resultado is not None or mesa.jogador_id is None:
        return
    jogador = repo.obter_jogador(mesa.jogador_id)
    if jogador is None:
        return
    resultado = economia.resultado_da_demo(jogador, mesa.estado, repo.fagulhas_ganhas_hoje(jogador.id))
    repo.registrar_partida(jogador.id, resultado)
    mesa.resultado = resultado


def _mensagem_do_fim(mesa: Mesa) -> str:
    r = mesa.resultado
    if r is None:
        return "Fim de partida!"
    sinal = "+" if r.variacao_rating >= 0 else ""
    aviso = " (limite diário de Fagulhas atingido)" if r.limite_atingido else ""
    return (
        f"Fim de partida! {mesa.apelido} ficou em {r.colocacao}º com {r.pontos} pontos: "
        f"+{r.fagulhas} Fagulhas{aviso}, rating {r.rating_antes} → {r.rating_depois} ({sinal}{r.variacao_rating})."
    )


def iniciar(repo: Repositorio, mesa: Mesa, apelido: str) -> RespostaPartida:
    jogador = buscar_por_apelido(repo, apelido)
    if jogador is None:
        return _sem_partida(f"Nenhum jogador com o apelido {apelido.strip()!r}. Nenhuma partida foi iniciada.")
    mesa.estado = tabuleiro.nova_partida()
    mesa.jogador_id = jogador.id
    mesa.apelido = jogador.apelido
    mesa.resultado = None
    return _resposta(
        mesa, True, f"Partida iniciada: você joga como {jogador.apelido}, na base (0,0). {mesa.estado.mensagem}"
    )


def ver(mesa: Mesa) -> RespostaPartida:
    if mesa.estado is not None and mesa.estado.terminou:
        return _resposta(mesa, True, _mensagem_do_fim(mesa))
    return _resposta(mesa, True)


def _depois_da_jogada(repo: Repositorio, mesa: Mesa) -> RespostaPartida:
    _gravar_se_terminou(repo, mesa)
    if mesa.estado is not None and mesa.estado.terminou:
        return _resposta(mesa, True, _mensagem_do_fim(mesa))
    return _resposta(mesa, True)


def jogar(repo: Repositorio, mesa: Mesa, peca: int, giros: int, linha: int, coluna: int) -> RespostaPartida:
    estado = mesa.estado
    if estado is None:
        return _sem_partida()
    if estado.terminou:
        return _resposta(mesa, False, "A partida já terminou. Use iniciar_partida para jogar outra.")
    if not 0 <= peca < len(estado.mao):
        return _resposta(mesa, False, f"Peça {peca} não existe: escolha de 0 a {len(estado.mao) - 1}.")

    original = estado.mao[peca].saidas
    tabuleiro.selecionar(estado, peca)
    for _ in range(giros % 4):
        tabuleiro.girar_selecionada(estado)
    if not tabuleiro.jogar_na_casa(estado, linha, coluna):
        # Recusada: a peça volta à orientação mostrada antes, e a vez não passa.
        estado.mao[peca].saidas = original
        return _resposta(mesa, False)
    return _depois_da_jogada(repo, mesa)


def passar(repo: Repositorio, mesa: Mesa) -> RespostaPartida:
    estado = mesa.estado
    if estado is None:
        return _sem_partida()
    if estado.terminou:
        return _resposta(mesa, False, "A partida já terminou. Use iniciar_partida para jogar outra.")
    tabuleiro.passar(estado)
    return _depois_da_jogada(repo, mesa)
