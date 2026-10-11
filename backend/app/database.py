<<<<<<< HEAD
import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import require_valid_settings

logger = logging.getLogger("touchgrass.database")


# Fails at startup with ONE readable message listing every missing or unsafe
# setting (DATABASE_URL, JWT_SECRET, GROQ_API_KEY, ...).
settings = require_valid_settings()

DATABASE_URL = settings.database_url


_engine_options = {
    "echo": settings.sql_echo,
    # Managed Postgres providers close idle connections; reconnect quietly.
    "pool_pre_ping": True,
}

if settings.is_sqlite:
    # SQLite is only used by the automated tests.
    _engine_options["connect_args"] = {"check_same_thread": False}
=======
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191


engine = create_engine(
    DATABASE_URL,
<<<<<<< HEAD
    **_engine_options,
=======
    echo=False,
    pool_pre_ping=True,
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create missing tables and safely add columns introduced
    by newer versions of TouchGrass.

<<<<<<< HEAD
    This is intentionally lightweight (no Alembic needed for the MVP).
    It only ever ADDS columns; it never drops or rewrites data.
    """

    from . import models  # noqa: F401  (registers every table on Base)

=======
    This is intentionally lightweight for local development.
    """

>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
    # Create tables that don't exist yet.
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)

    # ---------------------------------------------------------
    # users
    # ---------------------------------------------------------

    if "users" in inspector.get_table_names():
        user_columns = {
            column["name"]
            for column in inspector.get_columns("users")
        }

        if "created_at" not in user_columns:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        ALTER TABLE users
                        ADD COLUMN created_at
                        TIMESTAMP WITH TIME ZONE
                        DEFAULT CURRENT_TIMESTAMP
                        NOT NULL
                        """
                    )
                )

    # ---------------------------------------------------------
    # user_profiles
    # ---------------------------------------------------------

    if "user_profiles" in inspector.get_table_names():
        profile_columns = {
            column["name"]
            for column in inspector.get_columns("user_profiles")
        }

        with engine.begin() as connection:

            if "adventure_level" not in profile_columns:
                connection.execute(
                    text(
                        """
                        ALTER TABLE user_profiles
                        ADD COLUMN adventure_level VARCHAR
                        """
                    )
                )

            if "updated_at" not in profile_columns:
                connection.execute(
                    text(
                        """
                        ALTER TABLE user_profiles
                        ADD COLUMN updated_at
                        TIMESTAMP WITH TIME ZONE
                        DEFAULT CURRENT_TIMESTAMP
                        NOT NULL
                        """
                    )
                )

<<<<<<< HEAD
    # ---------------------------------------------------------
    # Any other NEW nullable column declared in models.py
    # (e.g. user_profiles.learned_notes) is added automatically,
    # so upgrading never needs a manual SQL step.
    # ---------------------------------------------------------

    inspector = inspect(engine)

    for table in Base.metadata.sorted_tables:
        if table.name not in inspector.get_table_names():
            continue

        existing = {
            column["name"]
            for column in inspector.get_columns(table.name)
        }

        for column in table.columns:
            if column.name in existing or not column.nullable:
                continue

            column_type = column.type.compile(dialect=engine.dialect)

            with engine.begin() as connection:
                connection.execute(
                    text(
                        f'ALTER TABLE "{table.name}" '
                        f'ADD COLUMN "{column.name}" {column_type}'
                    )
                )

            logger.info(
                "Added column %s.%s",
                table.name,
                column.name,
            )

=======
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191

def check_database_connection():
    """
    Verify that PostgreSQL is reachable.
    """

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    except Exception:
<<<<<<< HEAD
        return False
=======
        return False
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
