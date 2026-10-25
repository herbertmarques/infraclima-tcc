from pathlib import Path
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def database_url() -> str:
    configured = os.getenv("INFRACLIMA_DATABASE_URL")
    if configured:
        return configured
    return f"sqlite:///{Path(__file__).resolve().parents[1] / 'infraclima.db'}"


_DATABASE_URL = database_url()
_CONNECT_ARGS = {"check_same_thread": False} if _DATABASE_URL.startswith("sqlite:") else {}
engine = create_engine(_DATABASE_URL, connect_args=_CONNECT_ARGS)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
