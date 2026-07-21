from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection
from sqlalchemy.orm import sessionmaker


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL belum dikonfigurasi. "
        "Tambahkan DATABASE_URL ke file .env."
    )


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@contextmanager
def get_connection() -> Generator:
    """
    Provide a raw DBAPI connection for repositories that use
    cursor.execute().
    """

    connection = engine.raw_connection()

    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()