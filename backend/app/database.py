"""SQLite local; esquema administrado exclusivamente por Alembic."""

from app.config import DATABASE_URL, check_database, resolve_database_url
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


def make_engine(url):
    url = resolve_database_url(url)
    check_database(url)
    engine = create_engine(
        url,
        connect_args=(
            {"check_same_thread": False, "timeout": 15}
            if url.startswith("sqlite")
            else {}
        ),
    )
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

    return engine


engine = make_engine(DATABASE_URL)


def get_db():
    with Session(engine) as session:
        yield session
