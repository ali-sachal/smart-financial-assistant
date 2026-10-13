import os
import time
import datetime
from sqlalchemy.exc import SQLAlchemyError
from app.db.session import SessionLocal
from app.repositories.system import system_crud
from app.core.exceptions import Message

def check_db():
    start = time.perf_counter()
    try:
        db = SessionLocal()
        try:
            system_crud.check_connection(db)
        finally:
            db.close()
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {"ok": True, "latency_ms": latency_ms}
    except (SQLAlchemyError, Exception) as e:
        return {"ok": False, "error": Message.DATABASE_CONNECTION_ERROR, "details": str(e)}

def health_payload(request_id: str, app_start_time: float):
    db_check = check_db()
    all_ok = db_check.get("ok")
    payload = {
        "status": "ok" if all_ok else "degraded",
        "checks": {
            "db": db_check,
        },
        "info": {
            "env": os.getenv("ENVIRONMENT", "local"),
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "uptime_seconds": int(time.time() - app_start_time),
        },
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "request_id": request_id or "-",
    }
    return payload, all_ok
