"""Database engine/session for SapiSehat platform backend."""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sapisehat_dev.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def create_all_tables() -> None:
    from api import db_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _run_migrations()


def _run_migrations() -> None:
    """Apply incremental schema migrations idempotently."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    with engine.connect() as conn:
        # farmer_accounts.address
        result = conn.exec_driver_sql("PRAGMA table_info(farmer_accounts)")
        existing = {row[1] for row in result.fetchall()}
        if "address" not in existing:
            conn.exec_driver_sql("ALTER TABLE farmer_accounts ADD COLUMN address TEXT")
            conn.commit()
        # accounts.address
        result2 = conn.exec_driver_sql("PRAGMA table_info(accounts)")
        existing2 = {row[1] for row in result2.fetchall()}
        if "address" not in existing2:
            conn.exec_driver_sql("ALTER TABLE accounts ADD COLUMN address TEXT")
            conn.commit()
