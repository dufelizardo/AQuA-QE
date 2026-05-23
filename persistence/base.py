from __future__ import annotations
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str | None = None):
    url = database_url or os.getenv("DATABASE_URL", "sqlite:///./aqua_qe.db")
    connect_args: dict = {}
    kwargs: dict = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool

    engine = create_engine(url, connect_args=connect_args, **kwargs)

    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, _):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def build_session_factory(engine) -> sessionmaker:
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


def get_session(session_factory: sessionmaker):
    session: Session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all_tables(engine) -> None:
    import requirements.infrastructure.models  # noqa: F401
    import validation.infrastructure.models  # noqa: F401
    import testing.infrastructure.models  # noqa: F401
    import traceability.infrastructure.models  # noqa: F401
    import accessibility.infrastructure.models  # noqa: F401
    import quality.infrastructure.models  # noqa: F401
    import knowledge.infrastructure.models  # noqa: F401
    import ai_gateway.infrastructure.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
