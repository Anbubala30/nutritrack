"""
Database connection setup using SQLAlchemy.

We start with SQLite for local development (zero setup — it's just a file),
and switch to PostgreSQL for production by changing only the DATABASE_URL
env variable. Nothing else in the app needs to change, because SQLAlchemy
abstracts the actual SQL dialect away from us.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# connect_args is only needed for SQLite (it disallows multi-thread access
# by default). PostgreSQL doesn't need this.
connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """All ORM models (tables) will inherit from this."""

    pass


def get_db():
    """
    FastAPI dependency that provides a database session per-request,
    and guarantees it's closed afterward — even if an error occurs.

    Using `yield` here (rather than `return`) lets us run cleanup code
    after the request finishes. This is a common FastAPI pattern called
    a "dependency with cleanup."
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
