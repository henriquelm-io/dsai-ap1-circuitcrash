"""Tabelas do banco (SQLAlchemy 2). Só são usadas dentro de circuitcrash.dados.

O desenho segue docs/banco-de-dados.md. A coluna `ordem` mantém a mesma ordem
dos dados de exemplo da spec 001.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import CheckConstraint, Date, DateTime, Engine, ForeignKey, MetaData, String, Text, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Nomes previsíveis para as restrições, para as migrações funcionarem igual no SQLite e no PostgreSQL.
CONVENCAO = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCAO)


class TabelaAvatar(Base):
    __tablename__ = "avatares"
    __table_args__ = (
        CheckConstraint("raridade IN ('comum', 'raro', 'epico', 'lendario', 'exclusivo')", name="raridade"),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    ordem: Mapped[int]
    nome: Mapped[str] = mapped_column(String(60))
    raridade: Mapped[str] = mapped_column(String(20))
    descricao: Mapped[str] = mapped_column(String(200))
    cor: Mapped[str] = mapped_column(String(20))
    fundo: Mapped[str] = mapped_column(String(20))
    desenho: Mapped[str] = mapped_column(Text)


class TabelaJogador(Base):
    __tablename__ = "jogadores"
    __table_args__ = (CheckConstraint("fagulhas >= 0", name="fagulhas_nao_negativas"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    ordem: Mapped[int]
    apelido: Mapped[str] = mapped_column(String(40), unique=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    # Identificador estável da conta Google; preenchido pela spec de login.
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True)
    membro_desde: Mapped[date] = mapped_column(Date)
    fagulhas: Mapped[int] = mapped_column(default=0)
    rating: Mapped[int] = mapped_column(default=1200)
    partidas: Mapped[int] = mapped_column(default=0)
    vitorias: Mapped[int] = mapped_column(default=0)
    objetivos_capturados: Mapped[int] = mapped_column(default=0)
    avatar_id: Mapped[str | None] = mapped_column(ForeignKey("avatares.id"))


class TabelaInventario(Base):
    __tablename__ = "inventario"

    jogador_id: Mapped[str] = mapped_column(ForeignKey("jogadores.id", ondelete="CASCADE"), primary_key=True)
    avatar_id: Mapped[str] = mapped_column(ForeignKey("avatares.id"), primary_key=True)
    obtido_em: Mapped[datetime] = mapped_column(DateTime)


class TabelaPartida(Base):
    __tablename__ = "partidas"
    __table_args__ = (CheckConstraint("tipo IN ('ranqueada', 'casual')", name="tipo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(20))
    iniciada_em: Mapped[datetime] = mapped_column(DateTime)
    terminada_em: Mapped[datetime | None] = mapped_column(DateTime)


class TabelaParticipacao(Base):
    __tablename__ = "participacoes"
    __table_args__ = (CheckConstraint("colocacao BETWEEN 1 AND 4", name="colocacao"),)

    partida_id: Mapped[int] = mapped_column(ForeignKey("partidas.id", ondelete="CASCADE"), primary_key=True)
    jogador_id: Mapped[str] = mapped_column(ForeignKey("jogadores.id", ondelete="CASCADE"), primary_key=True)
    colocacao: Mapped[int]
    pontos: Mapped[int]
    variacao_rating: Mapped[int]
    fagulhas: Mapped[int]


class TabelaMissao(Base):
    __tablename__ = "missoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    ordem: Mapped[int]
    titulo: Mapped[str] = mapped_column(String(100))
    meta: Mapped[int]
    recompensa: Mapped[int]


class TabelaProgressoMissao(Base):
    __tablename__ = "progresso_missoes"

    jogador_id: Mapped[str] = mapped_column(ForeignKey("jogadores.id", ondelete="CASCADE"), primary_key=True)
    missao_id: Mapped[int] = mapped_column(ForeignKey("missoes.id", ondelete="CASCADE"), primary_key=True)
    dia: Mapped[date] = mapped_column(Date, primary_key=True)
    progresso: Mapped[int] = mapped_column(default=0)


class TabelaConquista(Base):
    __tablename__ = "conquistas"

    id: Mapped[int] = mapped_column(primary_key=True)
    ordem: Mapped[int]
    nome: Mapped[str] = mapped_column(String(100))
    meta: Mapped[int]


class TabelaProgressoConquista(Base):
    __tablename__ = "progresso_conquistas"

    jogador_id: Mapped[str] = mapped_column(ForeignKey("jogadores.id", ondelete="CASCADE"), primary_key=True)
    conquista_id: Mapped[int] = mapped_column(ForeignKey("conquistas.id", ondelete="CASCADE"), primary_key=True)
    progresso: Mapped[int] = mapped_column(default=0)


@event.listens_for(Engine, "connect")
def _ligar_chaves_estrangeiras(conexao: Any, _registro: Any) -> None:
    """O SQLite só respeita chaves estrangeiras com este PRAGMA, em cada conexão."""
    modulo = type(conexao).__module__
    if modulo.startswith(("sqlite3", "pysqlite")):
        cursor = conexao.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
