"""Servidor MCP do CircuitCrash: ranking e partida de demonstração (specs 011 e 012).

Rode com: uv run circuitcrash-mcp (o Claude Code inicia sozinho pelo .mcp.json).
Leitura: ver_ranking, posicao_do_jogador, ver_partida. Escrita: iniciar_partida,
jogar_peca, passar_vez. As permissões (allow/ask) ficam em .claude/settings.json.
O site publica o mesmo servidor em /mcp, sem gravar as partidas e com partida_id (spec 012).
"""

from __future__ import annotations

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.domain import tabuleiro
from circuitcrash.domain.modelos import PARTIDAS_PARA_RANKING
from circuitcrash.mcps import partida, ranking
from circuitcrash.mcps.comum import ESCRITA, SO_LEITURA, repositorio_do_ambiente
from circuitcrash.mcps.partida import Mesas, RespostaPartida
from circuitcrash.mcps.ranking import Posicao, Ranking

_REGRAS = f"""CircuitCrash: puzzle de circuitos por turnos para 4 jogadores.
Ranking: só entram jogadores com pelo menos {PARTIDAS_PARA_RANKING} partidas.
Partida de demonstração: tabuleiro {tabuleiro.TAMANHO}x{tabuleiro.TAMANHO}, linhas e colunas de 0 a \
{tabuleiro.TAMANHO - 1}. Você joga como "Você", com base em (0,0); a fonte de energia fica em (3,3).
Cada peça tem saídas N, E, S e W (norte = linha menor, leste = coluna maior). Um giro vira a peça 90 graus no \
sentido horário. Uma peça só pode ser colocada numa casa vazia se uma das saídas dela encontrar uma saída do seu \
circuito. Objetivos (bateria 3, lâmpada 2, núcleo 5 pontos) são capturados quando o seu circuito ligado à fonte \
chega a eles; os pontos de um objetivo, uma vez ganhos, não se perdem. A partida começa na rodada 6 e termina \
depois da rodada {tabuleiro.MAX_RODADAS}; se "Você" terminar ligado à fonte, ganha mais {tabuleiro.BONUS_ENERGIZADO} \
pontos (o bônus é só seu). Na demonstração, Lia, Bruno e Kai não jogam: o tabuleiro deles fica parado e só as suas \
jogadas mudam o placar."""
_GRAVA = "No fim, Fagulhas e rating são gravados para o jogador."
_NAO_GRAVA = (
    "Este é o servidor público: no fim, Fagulhas e rating são calculados e mostrados, mas o resultado não é "
    "gravado, e o perfil do jogador não muda."
)
_FLUXO_LOCAL = "Fluxo: iniciar_partida → ver_partida → jogar_peca ou passar_vez, até terminar."
_FLUXO_PUBLICO = (
    "Fluxo: iniciar_partida devolve um partida_id; passe esse mesmo partida_id em ver_partida, jogar_peca e "
    "passar_vez, até terminar. O servidor não lembra a partida sem ele."
)

PartidaId = Annotated[
    str,
    Field(
        description="O partida_id que iniciar_partida devolveu. Obrigatório no servidor público; "
        "no local, vazio usa a última partida iniciada."
    ),
]


def instrucoes(publico: bool = False) -> str:
    if publico:
        return f"{_REGRAS} {_NAO_GRAVA}\n{_FLUXO_PUBLICO}"
    return f"{_REGRAS} {_GRAVA}\n{_FLUXO_LOCAL}"


INSTRUCOES = instrucoes()


def criar_servidor(repo: Repositorio | None = None, *, publico: bool = False) -> MCPServer:
    """Sem repositório, usa o do .env (o mesmo banco do site).

    publico=True é o servidor do site (spec 012): não grava partidas e exige o partida_id.
    """
    dados = repo if repo is not None else repositorio_do_ambiente()
    mesas = Mesas(publico=publico)
    no_fim = "mostra o resultado, que não é gravado" if publico else "grava o resultado"
    servidor = MCPServer("circuitcrash", instructions=instrucoes(publico))

    # ---------- leitura ----------

    @servidor.tool(name="ver_ranking", annotations=SO_LEITURA)
    def ver_ranking(
        limite: Annotated[
            int, Field(description=f"Quantos jogadores mostrar, de 1 a {ranking.LIMITE_MAXIMO}.")
        ] = ranking.LIMITE_PADRAO,
    ) -> Ranking:
        """Mostra o ranking do CircuitCrash, do maior rating para o menor, com partidas e taxa de vitória.

        Use quando perguntarem quem lidera, pedirem a classificação ou quiserem comparar jogadores.
        Para um jogador específico, prefira posicao_do_jogador.
        """
        return ranking.ver_ranking(dados, limite)

    @servidor.tool(name="posicao_do_jogador", annotations=SO_LEITURA)
    def posicao_do_jogador(
        apelido: Annotated[str, Field(description="Apelido do jogador, como voltz_br (sem diferenciar maiúsculas).")],
    ) -> Posicao:
        """Diz a posição e o rating de um jogador no ranking, ou quantas partidas faltam para ele entrar.

        Use quando perguntarem sobre um jogador específico, e antes de iniciar_partida para conferir
        que o apelido existe e ver o rating de antes da partida.
        """
        return ranking.posicao_do_jogador(dados, apelido)

    @servidor.tool(name="ver_partida", annotations=SO_LEITURA)
    def ver_partida(partida_id: PartidaId = "") -> RespostaPartida:
        """Mostra a partida em andamento: rodada, placar, peças da mão, casas ocupadas e jogadas válidas.

        Use quando precisar decidir a próxima jogada (antes de cada jogar_peca) ou quando pedirem o placar.
        Não muda nada. Sem partida em andamento, avisa para usar iniciar_partida.
        """
        mesa = mesas.obter(partida_id)
        return partida.ver(mesa) if mesa else mesas.nao_encontrada(partida_id)

    # ---------- escrita ----------
    # As descrições destas tools dependem do modo, por isso vão em description e não na docstring.

    @servidor.tool(
        name="iniciar_partida",
        annotations=ESCRITA,
        description=(
            "Começa a partida de demonstração jogando como esse jogador e devolve o partida_id dela. "
            "Use quando pedirem para jogar uma partida. "
            + (
                "Servidor público: o resultado não é gravado. Passe o partida_id nas próximas chamadas."
                if publico
                else "A partida que estava em andamento fica para trás, sem gravar. "
                "No fim, o resultado é gravado para esse jogador."
            )
        ),
    )
    def iniciar_partida(
        apelido: Annotated[str, Field(description='Apelido do jogador que vai jogar como "Você".')],
    ) -> RespostaPartida:
        mesa = mesas.nova()
        resposta = partida.iniciar(dados, mesa, apelido)
        if not resposta["ativa"]:
            mesas.descartar(mesa)
        return resposta

    @servidor.tool(
        name="jogar_peca",
        annotations=ESCRITA,
        description=(
            "Faz a jogada da vez: coloca a peça da mão, girada, numa casa vazia ligada ao seu circuito. "
            "Use quando for a sua vez numa partida em andamento, de preferência com uma das jogadas_validas de "
            "ver_partida. Jogada recusada não gasta a vez. Numa casa que já tem peça, gira essa peça do tabuleiro "
            f"(gasta a vez). Na última rodada, {no_fim}."
        ),
    )
    def jogar_peca(
        peca: Annotated[int, Field(description="Índice da peça na mão, como em ver_partida (0 a 4).")],
        giros: Annotated[int, Field(description="Quantos giros de 90° no sentido horário antes de colocar (0 a 3).")],
        linha: Annotated[int, Field(description="Linha da casa, de 0 a 6.")],
        coluna: Annotated[int, Field(description="Coluna da casa, de 0 a 6.")],
        partida_id: PartidaId = "",
    ) -> RespostaPartida:
        mesa = mesas.obter(partida_id)
        return partida.jogar(dados, mesa, peca, giros, linha, coluna) if mesa else mesas.nao_encontrada(partida_id)

    @servidor.tool(
        name="passar_vez",
        annotations=ESCRITA,
        description=(
            "Passa a vez sem jogar. "
            f"Use quando não houver jogada válida ou nenhuma ajudar a pontuar. Na última rodada, {no_fim}."
        ),
    )
    def passar_vez(partida_id: PartidaId = "") -> RespostaPartida:
        mesa = mesas.obter(partida_id)
        return partida.passar(dados, mesa) if mesa else mesas.nao_encontrada(partida_id)

    return servidor


def main() -> None:
    criar_servidor().run("stdio")


if __name__ == "__main__":
    main()
