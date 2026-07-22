"""Alembic environment — migrations synchrones via psycopg2.

Stratégie :
- Alembic utilise psycopg2 (driver sync) pour les migrations.
- Le runtime FastAPI continue d'utiliser asyncpg (driver async).
- L'URL asyncpg est convertie automatiquement en URL psycopg2.

Ce fichier remplace le env.py généré par `alembic init`.
"""

import os
import sys
from logging.config import fileConfig

# ---------------------------------------------------------------------------
# sys.path — doit être fait AVANT d'importer les modules 'app'
# ---------------------------------------------------------------------------
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# ruff: noqa: E402  (imports after sys.path manipulation are intentional)
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool
from alembic import context
from app.db.base import Base
from app.models.user import User  # noqa: F401

# ---------------------------------------------------------------------------
# Chargement des variables d'environnement (.env)
# ---------------------------------------------------------------------------
load_dotenv(os.path.join(backend_dir, ".env"))

# ---------------------------------------------------------------------------
# Configuration Alembic (alembic.ini)
# ---------------------------------------------------------------------------
config = context.config

# Convertit postgresql+asyncpg:// → postgresql+psycopg2://
database_url = os.environ.get("DATABASE_URL", "")
sync_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")

# Extraire les paramètres host= et port= de la query string
socket_host = None
socket_port = None
if "?" in sync_url:
    base_url, query_str = sync_url.split("?", 1)
    sync_url = base_url
    params = {}
    for param in query_str.split("&"):
        if "=" in param:
            k, v = param.split("=", 1)
            params[k] = v
    socket_host = params.get("host")
    socket_port = params.get("port")

config.set_main_option("sqlalchemy.url", sync_url)

# Activation des logs via alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Migrations OFFLINE (génération SQL sans connexion à la BDD)
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """Lance les migrations en mode offline (génère du SQL pur)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Migrations ONLINE (connexion sync psycopg2 à PostgreSQL)
# ---------------------------------------------------------------------------

def run_migrations_online() -> None:
    """Lance les migrations en mode online avec psycopg2."""
    connect_args = {}
    if socket_host:
        connect_args["host"] = socket_host
    if socket_port:
        connect_args["port"] = int(socket_port)

    connectable = create_engine(
        sync_url,
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------------------------
# Dispatch offline / online
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
