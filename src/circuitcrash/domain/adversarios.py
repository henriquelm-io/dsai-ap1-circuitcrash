"""Adversários automáticos da partida de demonstração (spec 010).

Lia, Bruno e Kai jogam no nível "médio", pelas mesmas regras do jogador humano:
1. colocam a peça que captura um objetivo ou deixa o circuito mais perto do alvo:
   a fonte e, com o circuito já energizado, o objetivo livre mais próximo;
2. senão, giram uma peça própria que liga mais casas ao circuito;
3. senão, passam a vez.

Python puro: os desempates usam o sorteio com semente da partida.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from circuitcrash.domain import tabuleiro as t


class TipoJogada(StrEnum):
    COLOCAR = "colocar"
    GIRAR = "girar"
    PASSAR = "passar"


@dataclass(frozen=True)
class Jogada:
    tipo: TipoJogada
    linha: int = -1
    coluna: int = -1
    indice: int = -1  # peça da mão (só COLOCAR)
    saidas: str = ""  # orientação escolhida (só COLOCAR)


PASSAR = Jogada(TipoJogada.PASSAR)


def mao_do_jogador(estado: t.EstadoPartida, jogador: int) -> list[t.PecaMao]:
    return estado.mao if jogador == 0 else estado.maos_adversarios[jogador]


def _orientacoes(saidas: str) -> list[str]:
    """As orientações distintas de uma peça (a reta tem 2, o cruzamento 1)."""
    return list(dict.fromkeys(t.girar(saidas, vezes) for vezes in range(4)))


def jogadas_validas(estado: t.EstadoPartida, jogador: int) -> list[Jogada]:
    """Tudo o que o jogador pode fazer agora, na ordem do tabuleiro."""
    jogadas = []
    mao = mao_do_jogador(estado, jogador)
    for linha in range(t.TAMANHO):
        for coluna in range(t.TAMANHO):
            casa = estado.casa(linha, coluna)
            if casa.tipo is t.TipoCasa.PECA and casa.dono == jogador:
                jogadas.append(Jogada(TipoJogada.GIRAR, linha, coluna))
            elif casa.tipo is t.TipoCasa.VAZIA:
                for indice, peca in enumerate(mao):
                    for saidas in _orientacoes(peca.saidas):
                        if t.encosta_no_circuito(estado, linha, coluna, saidas, jogador):
                            jogadas.append(Jogada(TipoJogada.COLOCAR, linha, coluna, indice, saidas))
    jogadas.append(PASSAR)
    return jogadas


def eh_valida(estado: t.EstadoPartida, jogador: int, jogada: Jogada) -> bool:
    """Confere uma jogada pelas regras, sem depender de `jogadas_validas`."""
    if jogada.tipo is TipoJogada.PASSAR:
        return True
    if not (0 <= jogada.linha < t.TAMANHO and 0 <= jogada.coluna < t.TAMANHO):
        return False
    casa = estado.casa(jogada.linha, jogada.coluna)
    if jogada.tipo is TipoJogada.GIRAR:
        return casa.tipo is t.TipoCasa.PECA and casa.dono == jogador
    mao = mao_do_jogador(estado, jogador)
    return (
        casa.tipo is t.TipoCasa.VAZIA
        and 0 <= jogada.indice < len(mao)
        and jogada.saidas in _orientacoes(mao[jogada.indice].saidas)
        and t.encosta_no_circuito(estado, jogada.linha, jogada.coluna, jogada.saidas, jogador)
    )


def _copia(estado: t.EstadoPartida) -> t.EstadoPartida:
    casas = [[replace(casa) for casa in linha] for linha in estado.casas]
    return t.EstadoPartida(casas=casas, mao=[], pontos=list(estado.pontos))


def _mexer(estado: t.EstadoPartida, jogador: int, jogada: Jogada) -> list[str]:
    """Muda o tabuleiro e recalcula a energia; não mexe na mão. Devolve as capturas."""
    if jogada.tipo is TipoJogada.COLOCAR:
        t.colocar(estado, jogada.linha, jogada.coluna, jogada.saidas, jogador)
    elif jogada.tipo is TipoJogada.GIRAR:
        casa = estado.casa(jogada.linha, jogada.coluna)
        casa.saidas = t.girar(casa.saidas)
    else:
        return []
    return t.recalcular(estado)


SEM_CAMINHO = t.TAMANHO * t.TAMANHO


def _vizinhas(linha: int, coluna: int) -> list[tuple[int, int]]:
    return [
        (linha + dl, coluna + dc)
        for dl, dc in t.DIRECOES.values()
        if 0 <= linha + dl < t.TAMANHO and 0 <= coluna + dc < t.TAMANHO
    ]


def distancia_do_alvo(estado: t.EstadoPartida, jogador: int) -> int:
    """Quantas peças, no mínimo, faltam para o circuito tocar o próximo alvo.

    O alvo é a fonte; com o circuito energizado, são os objetivos que ele ainda
    não toca. Conta casas vazias a partir das saídas livres do circuito, sem
    olhar o formato das peças. SEM_CAMINHO se não há caminho; 0 sem alvo.
    """
    circuito, energizado, tocados = t.circuito_do_jogador(estado, jogador)
    if energizado:
        alvos = {
            (linha, coluna)
            for linha in range(t.TAMANHO)
            for coluna in range(t.TAMANHO)
            if estado.casa(linha, coluna).tipo is t.TipoCasa.OBJETIVO and (linha, coluna) not in tocados
        }
    else:
        alvos = {t.CENTRO}
    if not alvos:
        return 0
    fila = []
    for linha, coluna in circuito:
        for d in estado.casa(linha, coluna).saidas:
            dl, dc = t.DIRECOES[d]
            pos = (linha + dl, coluna + dc)
            if pos in _vizinhas(linha, coluna) and estado.casa(*pos).tipo is t.TipoCasa.VAZIA:
                fila.append(pos)
    distancias = dict.fromkeys(fila, 1)
    for pos in fila:  # busca em largura: a fila cresce enquanto é percorrida
        if any(vizinha in alvos for vizinha in _vizinhas(*pos)):
            return distancias[pos]
        for vizinha in _vizinhas(*pos):
            if vizinha not in distancias and estado.casa(*vizinha).tipo is t.TipoCasa.VAZIA:
                distancias[vizinha] = distancias[pos] + 1
                fila.append(vizinha)
    return SEM_CAMINHO


@dataclass(frozen=True)
class _Efeito:
    ganho: int
    energizado: bool
    distancia: int
    tamanho: int

    @property
    def progresso(self) -> tuple[bool, int]:
        """Energizar vale mais do que encurtar o caminho até o alvo."""
        return (self.energizado, -self.distancia)


def _medir(estado: t.EstadoPartida, jogador: int, ganho: int = 0) -> _Efeito:
    circuito, energizado, _ = t.circuito_do_jogador(estado, jogador)
    return _Efeito(ganho, energizado, distancia_do_alvo(estado, jogador), len(circuito))


def _efeito(estado: t.EstadoPartida, jogador: int, jogada: Jogada) -> _Efeito:
    simulado = _copia(estado)
    _mexer(simulado, jogador, jogada)
    return _medir(simulado, jogador, simulado.pontos[jogador] - estado.pontos[jogador])


def escolher_jogada(estado: t.EstadoPartida, jogador: int) -> Jogada:
    """Estratégia "médio": capturar ou chegar perto do alvo; senão girar; senão passar."""
    agora = _medir(estado, jogador)
    colocacoes: list[tuple[tuple[int, bool, int], Jogada]] = []
    giros: list[tuple[tuple[int, bool, int], Jogada]] = []
    for jogada in jogadas_validas(estado, jogador):
        if jogada.tipo is TipoJogada.PASSAR:
            continue
        efeito = _efeito(estado, jogador, jogada)
        if jogada.tipo is TipoJogada.COLOCAR:
            if efeito.ganho > 0 or efeito.progresso > agora.progresso:
                colocacoes.append(((efeito.ganho, *efeito.progresso), jogada))
        elif (efeito.ganho > 0 or efeito.tamanho > agora.tamanho) and efeito.energizado >= agora.energizado:
            giros.append(((efeito.ganho, efeito.energizado, efeito.tamanho), jogada))
    for candidatas in (colocacoes, giros):
        if candidatas:
            melhor = max(chave for chave, _ in candidatas)
            return estado.sorteio.choice([jogada for chave, jogada in candidatas if chave == melhor])
    return PASSAR


def aplicar(estado: t.EstadoPartida, jogador: int, jogada: Jogada) -> str:
    """Faz a jogada no estado da partida e devolve a linha do histórico."""
    nome = t.JOGADORES_DEMO[jogador].nome
    if not eh_valida(estado, jogador, jogada):
        raise ValueError(f"Jogada inválida de {nome}: {jogada}")
    if jogada.tipo is TipoJogada.PASSAR:
        return f"{nome} passou a vez"
    texto = f"{nome} girou a sua peça"
    if jogada.tipo is TipoJogada.COLOCAR:
        mao = mao_do_jogador(estado, jogador)
        peca = mao.pop(jogada.indice)
        mao.append(t.sortear_peca(estado.sorteio))
        texto = f"{nome} colocou uma {t.NOMES_FORMATO[peca.formato].lower()}"
    eventos = _mexer(estado, jogador, jogada)
    return "; ".join([texto, *eventos])


def jogar_adversarios(estado: t.EstadoPartida) -> None:
    """Lia, Bruno e Kai jogam, nessa ordem, e cada jogada entra no histórico."""
    for jogador in t.ADVERSARIOS:
        t.registrar(estado, aplicar(estado, jogador, escolher_jogada(estado, jogador)))
