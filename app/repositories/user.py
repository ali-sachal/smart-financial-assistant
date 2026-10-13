from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import Users, Plan, PlanDetail, Module
from sqlalchemy.orm import joinedload

class UserRepository:
    def get_by_user_id(self, db: Session, user_id: str) -> Optional[Users]:
        return db.query(Users).options(
            joinedload(Users.plan)
                .joinedload(Plan.details)
                .joinedload(PlanDetail.module)
        ).filter(Users.user_id == user_id).first()

    def create(self, db: Session, user: Users) -> Users:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update(self, db: Session, user: Users) -> Users:
        db.commit()
        db.refresh(user)
        return user

    def get_all_auto_sub_users(self, db: Session) -> List[Users]:
        return db.query(Users).filter(Users.auto_sub == True).all()
    
    def cancel_subscrption(self, db: Session, user_id, auto_sub) -> bool:
        db_user = db.query(Users).filter(Users.user_id == user_id).first()
        if db_user:
            db_user.auto_sub = auto_sub
            db.commit()
            db.refresh(db_user)
        return True
    
    def add_general_credits(self, db: Session, user: Users) -> Users:
        db.commit()
        db.refresh(user)
        return user

    def deduct_general_credits(self, db: Session, user: Users) -> Users:
        db.commit()
        db.refresh(user)
        return user
    
    def get_general_credits(self, db: Session, user_id):
        return (
            db.query(Users)
            .filter(Users.user_id == str(user_id))
            .first()
        )

        if result is None:
            return {
                "total_credits": 0,
                "credits_left": 0,
                "credits_used": 0,
            }

        return {
            "total_credits": result.total_general_credits,
            "credits_left": result.general_credits_left,
            "credits_used": result.general_credits_used,
        }

        
user_repository = UserRepository()
