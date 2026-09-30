"""
Manajemen Session dan Inisialisasi Database (SQLAlchemy)
"""
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .entities import Base

_engine = None
_SessionFactory = None

def init_db(database_uri: str):
    global _engine, _SessionFactory
    _engine = create_engine(database_uri, echo=False)
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
