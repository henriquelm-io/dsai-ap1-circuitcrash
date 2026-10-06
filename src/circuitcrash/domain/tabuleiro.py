"""Regras do tabuleiro do CircuitCrash usadas pela partida de demonstração.

Python puro: sem banco, sem rede, sem relógio. O sorteio de peças usa uma
semente, então a mesma partida sempre se repete igual.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import StrEnum

TAMANHO = 7
CENTRO = (3, 3)
MAX_RODADAS = 12
TAMANHO_MAO = 5
BONUS_ENERGIZADO = 3
SEMENTE_PADRAO = 42
LINHAS_HISTORICO = 8
ADVERSARIOS = (1, 2, 3)

DIRECOES: dict[str, tuple[int, int]] = {"N": (-1, 0), "E": (0, 1), "S": (1, 0), "W": (0, -1)}
OPOSTA = {"N": "S", "S": "N", "E": "W", "W": "E"}
GIRO_HORARIO = {"N": "E", "E": "S", "S": "W", "W": "N"}

# Formatos de peça: as saídas de cada uma.
FORMATOS: dict[str, str] = {
    "reta": "NS",
    "curva": "NE",
    "t": "NES",
    "cruzamento": "NESW",
}
NOMES_FORMATO = {"reta": "Reta", "curva": "Curva", "t": "Peça em T", "cruzamento": "Cruzamento"}


class TipoCasa(StrEnum):
    VAZIA = "vazia"
    PECA = "peca"
    FONTE = "fonte"
    BASE = "base"
    OBJETIVO = "objetivo"
    BLOQUEIO = "bloqueio"


@dataclass(frozen=True)
class Objetivo:
    nome: str
    pontos: int


OBJETIVOS = {
    "bateria": Objetivo("Bateria", 3),
    "lampada": Objetivo("Lâmpada", 2),
    "nucleo": Objetivo("Núcleo", 5),
}


@dataclass(frozen=True)
class Jogador:
    indice: int
    nome: str
    inicial: str
    cor: str
    base: tuple[int, int]


JOGADORES_DEMO = (
    Jogador(0, "Você", "V", "#F5A524", (0, 0)),
    Jogador(1, "Lia", "L", "#38BDF8", (0, 6)),
    Jogador(2, "Bruno", "B", "#A3E635", (6, 0)),
    Jogador(3, "Kai", "K", "#F472B6", (6, 6)),
)


def girar(saidas: str, vezes: int = 1) -> str:
    """Gira as saídas de uma peça 90° no sentido horário, `vezes` vezes."""
    atual = saidas
    for _ in range(vezes % 4):
        atual = "".join(GIRO_HORARIO[d] for d in atual)
    return "".join(sorted(atual, key="NESW".index))


@dataclass
class Casa:
    tipo: TipoCasa = TipoCasa.VAZIA
    saidas: str = ""
    dono: int | None = None
    objetivo: str | None = None
    capturado_por: int | None = None


@dataclass
class PecaMao:
    formato: str
    saidas: str


@dataclass
class EstadoPartida:
    casas: list[list[Casa]]
    mao: list[PecaMao]
    pontos: list[int]
    maos_adversarios: dict[int, list[PecaMao]] = field(default_factory=dict)
    rodada: int = 1
    selecionada: int = 0
    mensagem: str = "Escolha uma peça e toque numa casa vazia ao lado do seu circuito."
    erro: bool = False
    historico: list[str] = field(default_factory=list)
    energizados: set[tuple[int, int]] = field(default_factory=set)
    sorteio: random.Random = field(default_factory=lambda: random.Random(SEMENTE_PADRAO))

    @property
    def terminou(self) -> bool:
        return self.rodada > MAX_RODADAS

    def casa(self, linha: int, coluna: int) -> Casa:
        return self.casas[linha][coluna]


def _dentro(linha: int, coluna: int) -> bool:
    return 0 <= linha < TAMANHO and 0 <= coluna < TAMANHO


def _saidas_da_casa(casa: Casa) -> str:
    if casa.tipo in (TipoCasa.FONTE, TipoCasa.OBJETIVO):
        return "NESW"
    return casa.saidas


def sortear_peca(sorteio: random.Random) -> PecaMao:
    formato = sorteio.choice(["reta", "reta", "curva", "curva", "curva", "t", "cruzamento"])
    return PecaMao(formato, girar(FORMATOS[formato], sorteio.randrange(4)))


def colocar(estado: EstadoPartida, linha: int, coluna: int, saidas: str, dono: int) -> None:
    estado.casas[linha][coluna] = Casa(TipoCasa.PECA, saidas, dono)


def nova_partida(semente: int = SEMENTE_PADRAO) -> EstadoPartida:
    """Monta o tabuleiro de demonstração já no meio da partida (rodada 6).

    A semente decide as mãos e os desempates dos adversários: a mesma semente,
    com as mesmas jogadas, repete a mesma partida.
    """
    casas = [[Casa() for _ in range(TAMANHO)] for _ in range(TAMANHO)]
    estado = EstadoPartida(casas=casas, mao=[], pontos=[0, 0, 0, 0], rodada=6, sorteio=random.Random(semente))

    casas[3][3] = Casa(TipoCasa.FONTE)
    for j in JOGADORES_DEMO:
        linha, coluna = j.base
        saidas = ("S" if linha == 0 else "N") + ("E" if coluna == 0 else "W")
        casas[linha][coluna] = Casa(TipoCasa.BASE, girar(saidas, 0), j.indice)

    objetivos = {(1, 4): "bateria", (5, 1): "lampada", (5, 4): "nucleo", (3, 6): "lampada", (2, 1): "bateria"}
    for (linha, coluna), nome in objetivos.items():
        casas[linha][coluna] = Casa(TipoCasa.OBJETIVO, objetivo=nome)
    casas[4][4] = Casa(TipoCasa.BLOQUEIO)

    # Você: base (0,0) -> fonte, quase lá.
    colocar(estado, 0, 1, "EW", 0)
    colocar(estado, 0, 2, "SW", 0)
    colocar(estado, 1, 2, "NS", 0)
    colocar(estado, 2, 2, "NEW", 0)
    # Lia: chega à fonte e à bateria (1,4).
    colocar(estado, 1, 6, "NS", 1)
    colocar(estado, 2, 6, "NW", 1)
    colocar(estado, 2, 5, "EW", 1)
    colocar(estado, 2, 4, "NSE", 1)
    colocar(estado, 3, 4, "NW", 1)
    # Bruno: chega à fonte e encosta na lâmpada (5,1).
    colocar(estado, 5, 0, "NES", 2)
    colocar(estado, 4, 0, "ES", 2)
    colocar(estado, 4, 1, "EW", 2)
    colocar(estado, 4, 2, "EW", 2)
    colocar(estado, 4, 3, "NW", 2)
    # Kai: travado pelo isolante.
    colocar(estado, 6, 5, "EW", 3)
    colocar(estado, 6, 4, "NE", 3)

    estado.pontos = [4, 9, 6, 3]
    estado.mao = [sortear_peca(estado.sorteio) for _ in range(TAMANHO_MAO)]
    estado.mao[0] = PecaMao("curva", "SW")
    estado.maos_adversarios = {j: [sortear_peca(estado.sorteio) for _ in range(TAMANHO_MAO)] for j in ADVERSARIOS}
    recalcular(estado, pontuar=False)
    estado.historico = [
        "Kai usou Isolante na casa do meio-baixo",
        "Bruno energizou a Lâmpada (+2)",
        "Lia girou uma curva",
    ]
    return estado


def _vizinhos_conectados(estado: EstadoPartida, linha: int, coluna: int) -> list[tuple[int, int]]:
    """Casas ligadas a esta por saídas que se encontram dos dois lados."""
    resultado = []
    for d in _saidas_da_casa(estado.casa(linha, coluna)):
        dl, dc = DIRECOES[d]
        nl, nc = linha + dl, coluna + dc
        if not _dentro(nl, nc):
            continue
        vizinha = estado.casa(nl, nc)
        if OPOSTA[d] in _saidas_da_casa(vizinha):
            resultado.append((nl, nc))
    return resultado


def circuito_do_jogador(estado: EstadoPartida, jogador: int) -> tuple[set[tuple[int, int]], bool, set[tuple[int, int]]]:
    """Percorre o circuito a partir da base.

    Retorna (casas do circuito, se alcança a fonte, objetivos tocados).
    A energia só passa por peças do próprio jogador; fonte e objetivos são pontas.
    """
    base = JOGADORES_DEMO[jogador].base
    visitadas = {base}
    fila = [base]
    alcanca_fonte = False
    objetivos: set[tuple[int, int]] = set()
    while fila:
        atual = fila.pop()
        for vizinha in _vizinhos_conectados(estado, *atual):
            casa = estado.casa(*vizinha)
            if casa.tipo is TipoCasa.FONTE:
                alcanca_fonte = True
            elif casa.tipo is TipoCasa.OBJETIVO:
                objetivos.add(vizinha)
            elif casa.tipo is TipoCasa.PECA and casa.dono == jogador and vizinha not in visitadas:
                visitadas.add(vizinha)
                fila.append(vizinha)
    return visitadas, alcanca_fonte, objetivos


def recalcular(estado: EstadoPartida, pontuar: bool = True) -> list[str]:
    """Atualiza energia e capturas. Retorna as mensagens de captura."""
    eventos = []
    estado.energizados = set()
    capturas: dict[tuple[int, int], int] = {}
    for jogador in range(len(JOGADORES_DEMO)):
        circuito, energizado, objetivos = circuito_do_jogador(estado, jogador)
        if energizado:
            estado.energizados |= circuito
            for pos in objetivos:
                capturas.setdefault(pos, jogador)
    for linha in range(TAMANHO):
        for coluna in range(TAMANHO):
            casa = estado.casa(linha, coluna)
            if casa.tipo is not TipoCasa.OBJETIVO:
                continue
            novo_dono = capturas.get((linha, coluna))
            if novo_dono is not None and novo_dono != casa.capturado_por and casa.objetivo:
                objetivo = OBJETIVOS[casa.objetivo]
                if pontuar:
                    estado.pontos[novo_dono] += objetivo.pontos
                    eventos.append(f"{JOGADORES_DEMO[novo_dono].nome} capturou {objetivo.nome} (+{objetivo.pontos})")
            casa.capturado_por = novo_dono
    return eventos


def selecionar(estado: EstadoPartida, indice: int) -> None:
    if 0 <= indice < len(estado.mao):
        estado.selecionada = indice
        estado.erro = False
        estado.mensagem = f"{NOMES_FORMATO[estado.mao[indice].formato]} selecionada. Toque numa casa vazia."


def girar_selecionada(estado: EstadoPartida) -> None:
    if estado.mao:
        peca = estado.mao[estado.selecionada]
        peca.saidas = girar(peca.saidas)
        estado.erro = False
        estado.mensagem = "Peça girada. Agora escolha onde colocar."


def registrar(estado: EstadoPartida, texto: str) -> None:
    """Põe uma linha no topo do histórico, guardando só as mais recentes."""
    estado.historico.insert(0, texto)
    del estado.historico[LINHAS_HISTORICO:]


def _fim_do_turno(estado: EstadoPartida, texto: str) -> None:
    """Fecha a jogada do jogador 0: os adversários jogam e a rodada avança."""
    # Import aqui porque adversarios importa este módulo.
    from circuitcrash.domain import adversarios

    registrar(estado, texto)
    adversarios.jogar_adversarios(estado)
    estado.rodada += 1
    if estado.terminou:
        for jogador in range(len(JOGADORES_DEMO)):
            if circuito_do_jogador(estado, jogador)[1]:
                estado.pontos[jogador] += BONUS_ENERGIZADO
        estado.mensagem = "Fim de partida!"
    estado.erro = False


def jogar_na_casa(estado: EstadoPartida, linha: int, coluna: int) -> bool:
    """Ação do jogador 0 numa casa: coloca a peça selecionada (casa vazia) ou gira uma peça.

    Retorna True quando a jogada foi aceita.
    """
    if estado.terminou:
        return False
    if not _dentro(linha, coluna):
        return _recusar(estado, "Casa fora do tabuleiro.")
    casa = estado.casa(linha, coluna)

    if casa.tipo is TipoCasa.PECA:
        casa.saidas = girar(casa.saidas)
        eventos = recalcular(estado)
        dono = JOGADORES_DEMO[casa.dono].nome if casa.dono is not None else "?"
        texto = "Você girou a sua peça" if casa.dono == 0 else f"Você girou uma peça de {dono}"
        estado.mensagem = "; ".join(eventos) if eventos else texto + "."
        _fim_do_turno(estado, texto)
        return True

    if casa.tipo is not TipoCasa.VAZIA:
        return _recusar(estado, "Essa casa não aceita peças.")
    if not estado.mao:
        return _recusar(estado, "Sua mão está vazia.")

    peca = estado.mao[estado.selecionada]
    if not encosta_no_circuito(estado, linha, coluna, peca.saidas):
        return _recusar(estado, "A peça precisa se ligar ao seu circuito. Gire-a ou escolha outra casa.")

    colocar(estado, linha, coluna, peca.saidas, 0)
    estado.mao.pop(estado.selecionada)
    estado.mao.append(sortear_peca(estado.sorteio))
    estado.selecionada = min(estado.selecionada, len(estado.mao) - 1)
    eventos = recalcular(estado)
    estado.mensagem = "; ".join(eventos) if eventos else "Peça colocada."
    _fim_do_turno(estado, f"Você colocou uma {NOMES_FORMATO[peca.formato].lower()}")
    return True


def passar(estado: EstadoPartida) -> None:
    if not estado.terminou:
        estado.mensagem = "Você passou a vez."
        _fim_do_turno(estado, "Você passou a vez")


def encosta_no_circuito(estado: EstadoPartida, linha: int, coluna: int, saidas: str, jogador: int = 0) -> bool:
    """Se uma peça com estas saídas, nesta casa, se liga ao circuito do jogador."""
    circuito, _, _ = circuito_do_jogador(estado, jogador)
    for d in saidas:
        dl, dc = DIRECOES[d]
        nl, nc = linha + dl, coluna + dc
        if (nl, nc) in circuito and OPOSTA[d] in estado.casa(nl, nc).saidas:
            return True
    return False


def _recusar(estado: EstadoPartida, mensagem: str) -> bool:
    estado.mensagem = mensagem
    estado.erro = True
    return False


def classificacao(estado: EstadoPartida) -> list[tuple[int, Jogador, int]]:
    """Lista (colocação, jogador, pontos), do 1º ao 4º."""
    ordem = sorted(JOGADORES_DEMO, key=lambda j: (-estado.pontos[j.indice], j.indice))
    return [(i + 1, j, estado.pontos[j.indice]) for i, j in enumerate(ordem)]
