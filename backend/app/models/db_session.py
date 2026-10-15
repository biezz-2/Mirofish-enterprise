"""
Manajemen Session dan Inisialisasi Database (SQLAlchemy)
"""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .entities import Base

_engine = None
_SessionFactory = None

def init_db(database_uri: str = None):
    global _engine, _SessionFactory

    if database_uri is None:
        database_uri = os.environ.get("DATABASE_URI", "sqlite:///mirofish.db")

    is_postgres = database_uri.startswith("postgresql")

    if is_postgres:
        _engine = create_engine(
            database_uri,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600
        )
    else:
        _engine = create_engine(
            database_uri,
            echo=False,
            connect_args={"check_same_thread": False}
        )

    Base.metadata.create_all(_engine)
    _SessionFactory = scoped_session(sessionmaker(bind=_engine, expire_on_commit=False))
    return _engine

def get_engine():
    return _engine

@contextmanager
def get_db_session():
    if _SessionFactory is None:
        raise RuntimeError("Database belum diinisialisasi. Panggil init_db terlebih dahulu.")
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
