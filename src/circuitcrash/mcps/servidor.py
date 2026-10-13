"""Servidor MCP do CircuitCrash: ranking, partida de demonstração (spec 011) e loja (spec 012).

Rode com: uv run circuitcrash-mcp (o Claude Code inicia sozinho pelo .mcp.json).
Leitura: ver_ranking, posicao_do_jogador, ver_partida, consultar_loja. Escrita: iniciar_partida,
jogar_peca, passar_vez. As permissões (allow/ask) ficam em .claude/settings.json.
"""

from __future__ import annotations

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.domain import tabuleiro
from circuitcrash.domain.modelos import PARTIDAS_PARA_RANKING, PRECOS
from circuitcrash.mcps import loja, partida, ranking
from circuitcrash.mcps.comum import ESCRITA, SO_LEITURA, repositorio_do_ambiente
from circuitcrash.mcps.loja import RespostaLoja
from circuitcrash.mcps.partida import Mesa, RespostaPartida
from circuitcrash.mcps.ranking import Posicao, Ranking

_PRECOS = ", ".join(f"{raridade.rotulo} {preco}" for raridade, preco in PRECOS.items())

INSTRUCOES = f"""CircuitCrash: puzzle de circuitos por turnos para 4 jogadores.
Ranking: só entram jogadores com pelo menos {PARTIDAS_PARA_RANKING} partidas.
Partida de demonstração: tabuleiro {tabuleiro.TAMANHO}x{tabuleiro.TAMANHO}, linhas e colunas de 0 a \
{tabuleiro.TAMANHO - 1}. Você joga como "Você", com base em (0,0); a fonte de energia fica em (3,3).
Cada peça tem saídas N, E, S e W (norte = linha menor, leste = coluna maior). Um giro vira a peça 90 graus no \
sentido horário. Uma peça só pode ser colocada numa casa vazia se uma das saídas dela encontrar uma saída do seu \
circuito. Objetivos (bateria 3, lâmpada 2, núcleo 5 pontos) são capturados quando o seu circuito ligado à fonte \
chega a eles; os pontos de um objetivo, uma vez ganhos, não se perdem. A partida começa na rodada 6 e termina \
depois da rodada {tabuleiro.MAX_RODADAS}; se "Você" terminar ligado à fonte, ganha mais {tabuleiro.BONUS_ENERGIZADO} \
pontos (o bônus é só seu). Na demonstração, Lia, Bruno e Kai não jogam: o tabuleiro deles fica parado e só as suas \
jogadas mudam o placar. No fim, Fagulhas e rating são gravados para o jogador.
Fluxo: iniciar_partida → ver_partida → jogar_peca ou passar_vez, até terminar.
Loja: avatares comprados com Fagulhas por raridade ({_PRECOS}); os exclusivos não são vendidos. Pelo MCP a \
loja só é consultada (consultar_loja); comprar e equipar são feitos no site."""


def criar_servidor(repo: Repositorio | None = None) -> MCPServer:
    """Sem repositório, usa o do .env (o mesmo banco do site)."""
    dados = repo if repo is not None else repositorio_do_ambiente()
    mesa = Mesa()
    servidor = MCPServer("circuitcrash", instructions=INSTRUCOES)

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
    def ver_partida() -> RespostaPartida:
        """Mostra a partida em andamento: rodada, placar, peças da mão, casas ocupadas e jogadas válidas.

        Use quando precisar decidir a próxima jogada (antes de cada jogar_peca) ou quando pedirem o placar.
        Não muda nada. Sem partida em andamento, avisa para usar iniciar_partida.
        """
        return partida.ver(mesa)

    @servidor.tool(name="consultar_loja", annotations=SO_LEITURA)
    def consultar_loja(
        apelido: Annotated[str, Field(description="Apelido do jogador, como lia.ohm (sem diferenciar maiúsculas).")],
    ) -> RespostaLoja:
        """Mostra a loja de avatares para um jogador: Fagulhas, avatar equipado, avatares que ele possui e o
        catálogo com preço, raridade e o que ele consegue comprar agora (ou quanto falta).

        Use quando perguntarem quantas Fagulhas um jogador tem, quais avatares ele possui ou o que dá para
        comprar. Só consulta: não compra nem equipa; isso é feito no site, na tela /loja.
        """
        return loja.consultar_loja(dados, apelido)

    # ---------- escrita ----------

    @servidor.tool(name="iniciar_partida", annotations=ESCRITA)
    def iniciar_partida(
        apelido: Annotated[str, Field(description="Apelido do jogador que vai jogar; o resultado é gravado para ele.")],
    ) -> RespostaPartida:
        """Começa a partida de demonstração jogando como esse jogador.

        Use quando pedirem para jogar uma partida. Descarta, sem gravar, a partida que estiver em andamento.
        """
        return partida.iniciar(dados, mesa, apelido)

    @servidor.tool(name="jogar_peca", annotations=ESCRITA)
    def jogar_peca(
        peca: Annotated[int, Field(description="Índice da peça na mão, como em ver_partida (0 a 4).")],
        giros: Annotated[int, Field(description="Quantos giros de 90° no sentido horário antes de colocar (0 a 3).")],
        linha: Annotated[int, Field(description="Linha da casa, de 0 a 6.")],
        coluna: Annotated[int, Field(description="Coluna da casa, de 0 a 6.")],
    ) -> RespostaPartida:
        """Faz a jogada da vez: coloca a peça da mão, girada, numa casa vazia ligada ao seu circuito.

        Use quando for a sua vez numa partida em andamento, de preferência com uma das jogadas_validas de
        ver_partida. Jogada recusada não gasta a vez. Numa casa que já tem peça, gira essa peça do tabuleiro
        (gasta a vez). Na última rodada, grava o resultado.
        """
        return partida.jogar(dados, mesa, peca, giros, linha, coluna)

    @servidor.tool(name="passar_vez", annotations=ESCRITA)
    def passar_vez() -> RespostaPartida:
        """Passa a vez sem jogar.

        Use quando não houver jogada válida ou nenhuma ajudar a pontuar. Na última rodada, grava o resultado.
        """
        return partida.passar(dados, mesa)

    return servidor


def main() -> None:
    criar_servidor().run("stdio")


if __name__ == "__main__":
    main()
