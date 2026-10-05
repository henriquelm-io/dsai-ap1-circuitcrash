"""Cria as tabelas e carrega os dados de exemplo de dados/memoria.py no banco.

Uso:
    uv run python -m circuitcrash.dados.carga             # migra e carrega, se o banco estiver vazio
    uv run python -m circuitcrash.dados.carga --recriar   # apaga os dados e carrega de novo
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from circuitcrash.dados import memoria
from circuitcrash.dados.config import carregar_env, normalizar_url, url_do_banco
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

RAIZ = Path(__file__).resolve().parents[3]

# Ordem de remoção que respeita as chaves estrangeiras.
TABELAS_PARA_APAGAR = (
    TabelaProgressoMissao,
    TabelaProgressoConquista,
    TabelaParticipacao,
    TabelaInventario,
    TabelaPartida,
    TabelaMissao,
    TabelaConquista,
    TabelaJogador,
    TabelaAvatar,
)


def migrar(url: str) -> None:
    """Equivale a `alembic upgrade head` para a URL dada."""
    config = Config(str(RAIZ / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    config.attributes["configurar_log"] = False
    command.upgrade(config, "head")


def dia_do_resumo(quando: str, hoje: date) -> date:
    """Converte "hoje", "ontem" ou "dd/mm" de ResumoPartida.quando numa data."""
    if quando == "hoje":
        return hoje
    if quando == "ontem":
        return hoje - timedelta(days=1)
    dia, mes = (int(parte) for parte in quando.split("/"))
    data = date(hoje.year, mes, dia)
    return data if data <= hoje else data.replace(year=hoje.year - 1)


def _inserir_exemplo(s: Session, hoje: date) -> None:
    agora = datetime.combine(hoje, time(12, 0))
    exemplo = memoria.RepositorioMemoria()

    for ordem, a in enumerate(memoria.AVATARES, start=1):
        s.add(
            TabelaAvatar(
                id=a.id,
                ordem=ordem,
                nome=a.nome,
                raridade=a.raridade.value,
                descricao=a.descricao,
                cor=a.cor,
                fundo=a.fundo,
                desenho=a.desenho,
            )
        )
    s.flush()

    for ordem, j in enumerate(memoria.JOGADORES, start=1):
        s.add(
            TabelaJogador(
                id=j.id,
                ordem=ordem,
                apelido=j.apelido,
                email=j.email,
                membro_desde=j.membro_desde,
                fagulhas=j.fagulhas,
                rating=j.rating,
                partidas=j.partidas,
                vitorias=j.vitorias,
                objetivos_capturados=j.objetivos_capturados,
                avatar_id=j.avatar_id,
            )
        )
    s.flush()

    for jogador_id, avatares in memoria.INVENTARIOS.items():
        for avatar_id in sorted(avatares):
            s.add(TabelaInventario(jogador_id=jogador_id, avatar_id=avatar_id, obtido_em=agora))

    for jogador_id, resumos in memoria.PARTIDAS.items():
        for i, r in enumerate(resumos):
            # Minutos decrescentes mantêm a ordem da lista entre partidas do mesmo dia. Às 00:30,
            # uma partida jogada no dia da carga (spec 006) aparece antes das de exemplo de "hoje".
            terminada = datetime.combine(dia_do_resumo(r.quando, hoje), time(0, 30)) - timedelta(minutes=i)
            partida = TabelaPartida(
                tipo="ranqueada", iniciada_em=terminada - timedelta(minutes=15), terminada_em=terminada
            )
            s.add(partida)
            s.flush()
            s.add(
                TabelaParticipacao(
                    partida_id=partida.id,
                    jogador_id=jogador_id,
                    colocacao=r.colocacao,
                    pontos=r.pontos,
                    variacao_rating=r.variacao_rating,
                    fagulhas=r.fagulhas,
                )
            )

    primeiro = memoria.JOGADORES[0].id
    missoes = []
    for ordem, m in enumerate(exemplo.missoes_do_dia(primeiro), start=1):
        missao = TabelaMissao(ordem=ordem, titulo=m.titulo, meta=m.meta, recompensa=m.recompensa)
        s.add(missao)
        missoes.append(missao)
    conquistas = []
    for ordem, c in enumerate(exemplo.conquistas(primeiro), start=1):
        conquista = TabelaConquista(ordem=ordem, nome=c.nome, meta=c.meta)
        s.add(conquista)
        conquistas.append(conquista)
    s.flush()

    # O progresso vem das mesmas contas que o RepositorioMemoria faz.
    for j in memoria.JOGADORES:
        for missao, m in zip(missoes, exemplo.missoes_do_dia(j.id), strict=True):
            if m.progresso:
                s.add(TabelaProgressoMissao(jogador_id=j.id, missao_id=missao.id, dia=hoje, progresso=m.progresso))
        for conquista, c in zip(conquistas, exemplo.conquistas(j.id), strict=True):
            if c.progresso:
                s.add(TabelaProgressoConquista(jogador_id=j.id, conquista_id=conquista.id, progresso=c.progresso))


def carregar_exemplo(url: str, recriar: bool = False, hoje: date | None = None) -> bool:
    """Migra o banco e carrega os dados de exemplo. Devolve False se já havia dados."""
    url = normalizar_url(url)
    migrar(url)
    motor = create_engine(url)
    try:
        with Session(motor) as s, s.begin():
            if recriar:
                for tabela in TABELAS_PARA_APAGAR:
                    s.execute(delete(tabela))
            elif s.scalar(select(TabelaJogador.id).limit(1)) is not None:
                return False
            _inserir_exemplo(s, hoje or date.today())
        return True
    finally:
        motor.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria as tabelas e carrega os dados de exemplo do CircuitCrash.")
    parser.add_argument("--recriar", action="store_true", help="apaga todos os dados e carrega o exemplo de novo")
    args = parser.parse_args()

    carregar_env()
    url = url_do_banco()
    if not url:
        raise SystemExit("DATABASE_URL está vazia. Preencha no .env (ex.: sqlite:///circuitcrash.db).")
    if carregar_exemplo(url, recriar=args.recriar):
        print("Dados de exemplo carregados.")
    else:
        print("O banco já tem dados; nada foi alterado. Use --recriar para apagar e carregar de novo.")


if __name__ == "__main__":
    main()
