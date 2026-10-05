"""Tabelas iniciais da spec 002: jogadores, avatares, inventário, partidas, missões e conquistas.

Revisão: 0001
Anterior: nenhuma
Criada em: 04/10/2026
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "avatares",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=60), nullable=False),
        sa.Column("raridade", sa.String(length=20), nullable=False),
        sa.Column("descricao", sa.String(length=200), nullable=False),
        sa.Column("cor", sa.String(length=20), nullable=False),
        sa.Column("fundo", sa.String(length=20), nullable=False),
        sa.Column("desenho", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "raridade IN ('comum', 'raro', 'epico', 'lendario', 'exclusivo')", name=op.f("ck_avatares_raridade")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_avatares")),
    )
    op.create_table(
        "conquistas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("meta", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conquistas")),
    )
    op.create_table(
        "missoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(length=100), nullable=False),
        sa.Column("meta", sa.Integer(), nullable=False),
        sa.Column("recompensa", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_missoes")),
    )
    op.create_table(
        "partidas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("iniciada_em", sa.DateTime(), nullable=False),
        sa.Column("terminada_em", sa.DateTime(), nullable=True),
        sa.CheckConstraint("tipo IN ('ranqueada', 'casual')", name=op.f("ck_partidas_tipo")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_partidas")),
    )
    op.create_table(
        "jogadores",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("apelido", sa.String(length=40), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("google_sub", sa.String(length=255), nullable=True),
        sa.Column("membro_desde", sa.Date(), nullable=False),
        sa.Column("fagulhas", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("partidas", sa.Integer(), nullable=False),
        sa.Column("vitorias", sa.Integer(), nullable=False),
        sa.Column("objetivos_capturados", sa.Integer(), nullable=False),
        sa.Column("avatar_id", sa.String(length=40), nullable=True),
        sa.CheckConstraint("fagulhas >= 0", name=op.f("ck_jogadores_fagulhas_nao_negativas")),
        sa.ForeignKeyConstraint(["avatar_id"], ["avatares.id"], name=op.f("fk_jogadores_avatar_id_avatares")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jogadores")),
        sa.UniqueConstraint("apelido", name=op.f("uq_jogadores_apelido")),
        sa.UniqueConstraint("email", name=op.f("uq_jogadores_email")),
        sa.UniqueConstraint("google_sub", name=op.f("uq_jogadores_google_sub")),
    )
    op.create_table(
        "inventario",
        sa.Column("jogador_id", sa.String(length=40), nullable=False),
        sa.Column("avatar_id", sa.String(length=40), nullable=False),
        sa.Column("obtido_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["avatar_id"], ["avatares.id"], name=op.f("fk_inventario_avatar_id_avatares")),
        sa.ForeignKeyConstraint(
            ["jogador_id"], ["jogadores.id"], name=op.f("fk_inventario_jogador_id_jogadores"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("jogador_id", "avatar_id", name=op.f("pk_inventario")),
    )
    op.create_table(
        "participacoes",
        sa.Column("partida_id", sa.Integer(), nullable=False),
        sa.Column("jogador_id", sa.String(length=40), nullable=False),
        sa.Column("colocacao", sa.Integer(), nullable=False),
        sa.Column("pontos", sa.Integer(), nullable=False),
        sa.Column("variacao_rating", sa.Integer(), nullable=False),
        sa.Column("fagulhas", sa.Integer(), nullable=False),
        sa.CheckConstraint("colocacao BETWEEN 1 AND 4", name=op.f("ck_participacoes_colocacao")),
        sa.ForeignKeyConstraint(
            ["jogador_id"], ["jogadores.id"], name=op.f("fk_participacoes_jogador_id_jogadores"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["partida_id"], ["partidas.id"], name=op.f("fk_participacoes_partida_id_partidas"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("partida_id", "jogador_id", name=op.f("pk_participacoes")),
    )
    op.create_table(
        "progresso_conquistas",
        sa.Column("jogador_id", sa.String(length=40), nullable=False),
        sa.Column("conquista_id", sa.Integer(), nullable=False),
        sa.Column("progresso", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["conquista_id"],
            ["conquistas.id"],
            name=op.f("fk_progresso_conquistas_conquista_id_conquistas"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["jogador_id"],
            ["jogadores.id"],
            name=op.f("fk_progresso_conquistas_jogador_id_jogadores"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("jogador_id", "conquista_id", name=op.f("pk_progresso_conquistas")),
    )
    op.create_table(
        "progresso_missoes",
        sa.Column("jogador_id", sa.String(length=40), nullable=False),
        sa.Column("missao_id", sa.Integer(), nullable=False),
        sa.Column("dia", sa.Date(), nullable=False),
        sa.Column("progresso", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["jogador_id"], ["jogadores.id"], name=op.f("fk_progresso_missoes_jogador_id_jogadores"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["missao_id"], ["missoes.id"], name=op.f("fk_progresso_missoes_missao_id_missoes"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("jogador_id", "missao_id", "dia", name=op.f("pk_progresso_missoes")),
    )


def downgrade() -> None:
    op.drop_table("progresso_missoes")
    op.drop_table("progresso_conquistas")
    op.drop_table("participacoes")
    op.drop_table("inventario")
    op.drop_table("jogadores")
    op.drop_table("partidas")
    op.drop_table("missoes")
    op.drop_table("conquistas")
    op.drop_table("avatares")
