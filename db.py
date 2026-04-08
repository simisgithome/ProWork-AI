"""Database setup and helpers for AlloyDB connection."""

import os
from datetime import datetime

from sqlalchemy import create_engine

DB_USER = os.getenv("ALLOYDB_USER", "postgres")
DB_PASSWORD = os.getenv("ALLOYDB_PASSWORD", "alloydb")
DB_HOST = os.getenv("ALLOYDB_HOST", "10.119.0.2")
DB_PORT = os.getenv("ALLOYDB_PORT", "5432")
DB_NAME = os.getenv("ALLOYDB_DB", "postgres")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine


def serialize(obj):
    """Convert datetime objects to strings for LLM consumption."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize(i) for i in obj]
    return obj
