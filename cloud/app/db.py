"""Database engine/session (PRD section 9.1).

Uses SQLAlchemy so the same code runs against Supabase/Postgres in production
(set DATABASE_URL=postgresql+psycopg://...) and a local SQLite file for dev/demo
(the default). JSON columns use SQLAlchemy's portable JSON type.
"""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get("ACRE_DATABASE_URL", "sqlite:///./acre_cloud.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from . import models  # noqa: F401  (register models)

    Base.metadata.create_all(bind=engine)
