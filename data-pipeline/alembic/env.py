import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the project root to the path so we can import our models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Base and all models
from app.models.base import Base
from app.models.raw.award_raw import AwardRaw
from app.models.normalized.contracting_authority import ContractingAuthority
from app.models.normalized.supplier import Supplier
from app.models.normalized.procurement_procedure import ProcurementProcedure
from app.models.normalized.award import Award
from app.models.normalized.award_supplier import AwardSupplier
from app.models.raw.company import Company, CompanyRelation, CompanyImportSkip
from app.config.config import ConfigLoader

# Alembic Config object
config = context.config

# Load database URL from scraper config file
app_config = ConfigLoader.load("ba_awards_config.json")
database_url = app_config.get("database_url")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
else:
    raise ValueError("database_url not found in ba_awards_config.json")

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData object for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
