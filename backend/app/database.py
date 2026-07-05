"""Database engine, session management, and declarative base."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Imported models register themselves on Base.metadata."""
    from app import models  # noqa: F401  (ensure models are imported)

    Base.metadata.create_all(bind=engine)
    _run_lightweight_migrations()


def _run_lightweight_migrations() -> None:
    """Additive, idempotent column migrations for SQLite dev databases.

    create_all() never adds columns to pre-existing tables, so newly introduced
    columns are patched in here to avoid breaking older local databases.
    """
    if not settings.database_url.startswith("sqlite"):
        return
    from sqlalchemy import text

    additions = {
        "diagnoses": [("subject", "VARCHAR(20) DEFAULT 'plant'")],
        "users": [
            ("role", "VARCHAR(20) DEFAULT 'farmer'"),
            ("firebase_uid", "VARCHAR(128)"),
        ],
        "posts": [
            ("author_name", "VARCHAR(255) DEFAULT ''"),
            ("author_role", "VARCHAR(20) DEFAULT 'farmer'"),
        ],
        "comments": [("author_role", "VARCHAR(20) DEFAULT 'farmer'")],
    }
    with engine.begin() as conn:
        for table, columns in additions.items():
            existing = {
                row[1]
                for row in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
            }
            for name, ddl in columns:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
