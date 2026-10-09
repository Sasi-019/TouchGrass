import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")


engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
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

    This is intentionally lightweight for local development.
    """

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


def check_database_connection():
    """
    Verify that PostgreSQL is reachable.
    """

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    except Exception:
        return False