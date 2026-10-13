# app/db/session.py
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
import time
import logging
import json


from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_db_logger = logging.getLogger("db")

@event.listens_for(engine, "before_cursor_execute")
def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", time.perf_counter())

@event.listens_for(engine, "after_cursor_execute")
def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    start = conn.info.pop("query_start_time", None)
    if start is not None:
        duration_ms = int((time.perf_counter() - start) * 1000)
        _db_logger.info(json.dumps({"event": "db_query", "duration_ms": duration_ms, "rowcount": cursor.rowcount}))
