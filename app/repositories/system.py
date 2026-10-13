from sqlalchemy.orm import Session
from sqlalchemy import text

class SystemCRUD:
    def check_connection(self, db: Session) -> bool:
        try:
            db.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

system_crud = SystemCRUD()
