"""Repositório com banco de dados (SQLAlchemy 2).

Implementa circuitcrash.dados.repositorio.Repositorio. Cada método abre a própria
sessão e devolve dataclasses novas de domain/modelos.py; quem altera um Jogador
precisa chamar salvar_jogador para gravar. Detalhes em specs/002-banco-de-dados/.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta

from sqlalchemy import create_engine, func, select, update
from sqlalchemy.orm import sessionmaker

from circuitcrash.dados.config import normalizar_url
from circuitcrash.dados.tabelas import (
    TabelaAvatar,
    TabelaConquista,
    TabelaInventario,
    TabelaJogador,
    TabelaMissao,
    TabelaParticipacao,
    TabelaPartida,
    TabelaProgressoConquista,
    TabelaProgressoMissao,
)
from circuitcrash.domain.modelos import (
    PARTIDAS_PARA_RANKING,
    Avatar,
    Conquista,
    Jogador,
    Missao,
    Raridade,
    ResultadoPartida,
    ResumoPartida,
)

# Campos do Jogador copiados para a tabela ao salvar (google_sub e ordem ficam de fora).
CAMPOS_JOGADOR = (
    "apelido",
    "email",
    "membro_desde",
    "fagulhas",
    "rating",
    "partidas",
    "vitorias",
    "objetivos_capturados",
    "avatar_id",
)


def descrever_dia(dia: date, hoje: date) -> str:
    """ "hoje", "ontem" ou "dd/mm", como em ResumoPartida.quando."""
    if dia == hoje:
        return "hoje"
    if dia == hoje - timedelta(days=1):
        return "ontem"
    return dia.strftime("%d/%m")


def _jogador(linha: TabelaJogador) -> Jogador:
    return Jogador(
        linha.id,
        linha.apelido,
        linha.email,
        linha.membro_desde,
        fagulhas=linha.fagulhas,
        rating=linha.rating,
        partidas=linha.partidas,
        vitorias=linha.vitorias,
        objetivos_capturados=linha.objetivos_capturados,
        avatar_id=linha.avatar_id,
    )


def _avatar(linha: TabelaAvatar) -> Avatar:
    return Avatar(
        linha.id,
        linha.nome,
        Raridade(linha.raridade),
        linha.descricao,
        linha.cor,
        linha.fundo,
        linha.desenho,
    )


class RepositorioSQL:
    """Implementa circuitcrash.dados.repositorio.Repositorio com SQLite ou PostgreSQL."""

    def __init__(
        self,
        url: str,
        hoje: Callable[[], date] = date.today,
        agora: Callable[[], datetime] | None = None,
    ) -> None:
        self.motor = create_engine(normalizar_url(url))
        self._sessao = sessionmaker(self.motor)
        self._hoje = hoje
        # Sem relógio próprio, a hora atual vai no dia de hoje(), para os testes com dia fixo.
        self._agora = agora or (lambda: datetime.combine(self._hoje(), datetime.now().time()))

    def fechar(self) -> None:
        self.motor.dispose()

    # Jogadores

    def obter_jogador(self, jogador_id: str) -> Jogador | None:
        with self._sessao() as s:
            linha = s.get(TabelaJogador, jogador_id)
            return _jogador(linha) if linha else None

    def listar_jogadores(self) -> list[Jogador]:
        with self._sessao() as s:
            return [_jogador(linha) for linha in s.scalars(select(TabelaJogador).order_by(TabelaJogador.ordem))]

    def salvar_jogador(self, jogador: Jogador) -> None:
        with self._sessao.begin() as s:
            linha = s.get(TabelaJogador, jogador.id)
            if linha is None:
                ultima = s.scalar(select(func.max(TabelaJogador.ordem))) or 0
                linha = TabelaJogador(id=jogador.id, ordem=ultima + 1)
                s.add(linha)
            for campo in CAMPOS_JOGADOR:
                setattr(linha, campo, getattr(jogador, campo))

    def ranking(self, limite: int = 10) -> list[Jogador]:
        consulta = (
            select(TabelaJogador)
            .where(TabelaJogador.partidas >= PARTIDAS_PARA_RANKING)
            .order_by(TabelaJogador.rating.desc(), TabelaJogador.ordem)
            .limit(limite)
        )
        with self._sessao() as s:
            return [_jogador(linha) for linha in s.scalars(consulta)]

    # Avatares e inventário

    def listar_avatares(self) -> list[Avatar]:
        with self._sessao() as s:
            return [_avatar(linha) for linha in s.scalars(select(TabelaAvatar).order_by(TabelaAvatar.ordem))]

    def obter_avatar(self, avatar_id: str) -> Avatar | None:
        with self._sessao() as s:
            linha = s.get(TabelaAvatar, avatar_id)
            return _avatar(linha) if linha else None

    def inventario(self, jogador_id: str) -> set[str]:
        consulta = select(TabelaInventario.avatar_id).where(TabelaInventario.jogador_id == jogador_id)
        with self._sessao() as s:
            return set(s.scalars(consulta))

    def adicionar_ao_inventario(self, jogador_id: str, avatar_id: str) -> None:
        with self._sessao.begin() as s:
            if s.get(TabelaInventario, (jogador_id, avatar_id)) is None:
                s.add(TabelaInventario(jogador_id=jogador_id, avatar_id=avatar_id, obtido_em=datetime.now()))

    # Histórico e progresso

    def partidas_recentes(self, jogador_id: str, limite: int = 5) -> list[ResumoPartida]:
        consulta = (
            select(TabelaParticipacao, TabelaPartida.terminada_em)
            .join(TabelaPartida, TabelaPartida.id == TabelaParticipacao.partida_id)
            .where(TabelaParticipacao.jogador_id == jogador_id, TabelaPartida.terminada_em.is_not(None))
            .order_by(TabelaPartida.terminada_em.desc(), TabelaPartida.id.desc())
            .limit(limite)
        )
        hoje = self._hoje()
        with self._sessao() as s:
            return [
                ResumoPartida(
                    p.colocacao,
                    p.pontos,
                    p.variacao_rating,
                    p.fagulhas,
                    descrever_dia(terminada_em.date(), hoje) if terminada_em else "",
                )
                for p, terminada_em in s.execute(consulta)
            ]

    def missoes_do_dia(self, jogador_id: str) -> list[Missao]:
        consulta = (
            select(TabelaMissao, TabelaProgressoMissao.progresso)
            .outerjoin(
                TabelaProgressoMissao,
                (TabelaProgressoMissao.missao_id == TabelaMissao.id)
                & (TabelaProgressoMissao.jogador_id == jogador_id)
                & (TabelaProgressoMissao.dia == self._hoje()),
            )
            .order_by(TabelaMissao.ordem)
        )
        with self._sessao() as s:
            return [Missao(m.titulo, progresso or 0, m.meta, m.recompensa) for m, progresso in s.execute(consulta)]

    def conquistas(self, jogador_id: str) -> list[Conquista]:
        consulta = (
            select(TabelaConquista, TabelaProgressoConquista.progresso)
            .outerjoin(
                TabelaProgressoConquista,
                (TabelaProgressoConquista.conquista_id == TabelaConquista.id)
                & (TabelaProgressoConquista.jogador_id == jogador_id),
            )
            .order_by(TabelaConquista.ordem)
        )
        with self._sessao() as s:
            return [Conquista(c.nome, progresso or 0, c.meta) for c, progresso in s.execute(consulta)]

    # Partidas terminadas (spec 006)

    def fagulhas_ganhas_hoje(self, jogador_id: str) -> int:
        inicio = datetime.combine(self._hoje(), datetime.min.time())
        consulta = (
            select(func.coalesce(func.sum(TabelaParticipacao.fagulhas), 0))
            .join(TabelaPartida, TabelaPartida.id == TabelaParticipacao.partida_id)
            .where(
                TabelaParticipacao.jogador_id == jogador_id,
                TabelaPartida.terminada_em >= inicio,
                TabelaPartida.terminada_em < inicio + timedelta(days=1),
            )
        )
        with self._sessao() as s:
            return int(s.scalar(consulta) or 0)

    def registrar_partida(self, jogador_id: str, resultado: ResultadoPartida) -> None:
        agora = self._agora()
        with self._sessao.begin() as s:
            if s.get(TabelaJogador, jogador_id) is None:
                raise ValueError(f"Jogador não encontrado: {jogador_id}.")
            partida = TabelaPartida(tipo=resultado.tipo.value, iniciada_em=agora, terminada_em=agora)
            s.add(partida)
            s.flush()
            s.add(
                TabelaParticipacao(
                    partida_id=partida.id,
                    jogador_id=jogador_id,
                    colocacao=resultado.colocacao,
                    pontos=resultado.pontos,
                    variacao_rating=resultado.variacao_rating,
                    fagulhas=resultado.fagulhas,
                )
            )
            s.flush()
            # Soma ao valor do banco, para não apagar uma compra feita ao mesmo tempo.
            s.execute(
                update(TabelaJogador)
                .where(TabelaJogador.id == jogador_id)
                .values(
                    fagulhas=TabelaJogador.fagulhas + resultado.fagulhas,
                    rating=TabelaJogador.rating + resultado.variacao_rating,
                    partidas=TabelaJogador.partidas + 1,
                    vitorias=TabelaJogador.vitorias + int(resultado.vitoria),
                    objetivos_capturados=TabelaJogador.objetivos_capturados + resultado.objetivos,
                )
            )

    # Conta Google (spec 008)

    def obter_jogador_por_google(self, google_sub: str) -> Jogador | None:
        with self._sessao() as s:
            linha = s.scalar(select(TabelaJogador).where(TabelaJogador.google_sub == google_sub))
            return _jogador(linha) if linha else None

    def obter_jogador_por_email(self, email: str) -> Jogador | None:
        consulta = select(TabelaJogador).where(func.lower(TabelaJogador.email) == email.strip().lower())
        with self._sessao() as s:
            linha = s.scalar(consulta)
            return _jogador(linha) if linha else None

    def criar_jogador_google(self, jogador: Jogador, google_sub: str) -> None:
        with self._sessao.begin() as s:
            ultima = s.scalar(select(func.max(TabelaJogador.ordem))) or 0
            linha = TabelaJogador(id=jogador.id, ordem=ultima + 1, google_sub=google_sub)
            for campo in CAMPOS_JOGADOR:
                setattr(linha, campo, getattr(jogador, campo))
            s.add(linha)

    def vincular_google(self, jogador_id: str, google_sub: str) -> bool:
        with self._sessao.begin() as s:
            linha = s.get(TabelaJogador, jogador_id)
            if linha is None:
                return False
            if linha.google_sub is not None:
                return linha.google_sub == google_sub
            if s.scalar(select(TabelaJogador.id).where(TabelaJogador.google_sub == google_sub)) is not None:
                return False
            linha.google_sub = google_sub
            return True
