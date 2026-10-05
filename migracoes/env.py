"""Ambiente do Alembic do CircuitCrash.

A URL vem de `sqlalchemy.url` quando quem chama já a definiu (testes e carga);
senão, de DATABASE_URL no ambiente ou no .env.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from circuitcrash.dados.config import carregar_env, normalizar_url, url_do_banco
from circuitcrash.dados.tabelas import Base

config = context.config
if config.config_file_name is not None and config.attributes.get("configurar_log", True):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _url() -> str:
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return normalizar_url(url)
    carregar_env()
    url = url_do_banco()
    if not url:
        raise SystemExit("DATABASE_URL está vazia. Preencha no .env (ex.: sqlite:///circuitcrash.db).")
    return url


def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    motor = create_engine(_url())
    with motor.connect() as conexao:
        # render_as_batch permite alterar tabelas no SQLite, que não suporta ALTER completo.
        context.configure(connection=conexao, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()
    motor.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
