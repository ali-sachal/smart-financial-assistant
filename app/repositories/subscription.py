from sqlalchemy.orm import Session, joinedload
from app.models.subscription import Plan, Module, PlanDetail, UserSubscription
from app.models.user import Users
from typing import List, Optional
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from sqlalchemy import desc, exists, extract, func

class PlanRepository:
    def create(self, db: Session, plan: Plan) -> Plan:
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    def get_by_id(self, db: Session, plan_id: int) -> Optional[Plan]:
        return db.query(Plan).filter(Plan.id == plan_id).first()

    def get_all(self, db: Session) -> List[Plan]:
        return db.query(Plan).filter(Plan.status == True).all()

    def update(self, db: Session, plan: Plan) -> Plan:
        db.commit()
        db.refresh(plan)
        return plan

    def delete(self, db: Session, plan_id: int) -> bool:
        plan = self.get_by_id(db, plan_id)
        if plan:
            db.delete(plan)
            db.commit()
            return True
        return False

class ModuleRepository:
    def create(self, db: Session, module: Module) -> Module:
        db.add(module)
        db.commit()
        db.refresh(module)
        return module
        
    def get_by_id(self, db: Session, module_id: int) -> Optional[Module]:
        return db.query(Module).filter(Module.id == module_id).first()

    def get_by_slug(self, db: Session, slug: str) -> Optional[Module]:
        return db.query(Module).filter(Module.slug == slug).first()
        
    def get_all(self, db: Session) -> List[Module]:
        return db.query(Module).all()

    def update(self, db: Session, module: Module) -> Module:
        db.commit()
        db.refresh(module)
        return module

class UserSubscriptionRepository:
    def create(self, db: Session, sub: UserSubscription) -> UserSubscription:
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub

    def get_by_user_id(self, db: Session, user_id: str) -> Optional[UserSubscription]:
        return db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()
    
    def get_all_by_user_id(self, db: Session, user_id: str) -> List[UserSubscription]:
        return db.query(UserSubscription).filter(UserSubscription.user_id == user_id).all()
    def get_latest_any_by_user_id(self, db: Session, user_id: str) -> Optional[UserSubscription]:
        return (
            db.query(UserSubscription)
            .filter(UserSubscription.user_id == str(user_id))
            .order_by(UserSubscription.purchase_at.desc())
            .first()
        )

    def get_failed_or_pending_latest_purchase_expired_paid_user_ids(
        self,
        db: Session,
        cutoff: datetime,
    ) -> List[str]:
        latest_subscriptions = (
            db.query(
                UserSubscription.user_id.label("user_id"),
                UserSubscription.payment_status.label("payment_status"),
                func.row_number()
                .over(
                    partition_by=UserSubscription.user_id,
                    order_by=UserSubscription.purchase_at.desc(),
                )
                .label("row_number"),
            )
            .subquery()
        )

        paid_subscription_exists = exists().where(
            UserSubscription.user_id == Users.user_id,
            UserSubscription.payment_status == "paid",
        )

        unexpired_paid_subscription_exists = exists().where(
            UserSubscription.user_id == Users.user_id,
            UserSubscription.payment_status == "paid",
            UserSubscription.expiry_at >= cutoff,
        )

        return [
            row.user_id
            for row in (
                db.query(Users.user_id)
                .join(latest_subscriptions, latest_subscriptions.c.user_id == Users.user_id)
                .filter(
                    latest_subscriptions.c.row_number == 1,
                    latest_subscriptions.c.payment_status.in_(("failed", "pending")),
                    paid_subscription_exists,
                    ~unexpired_paid_subscription_exists,
                )
                .all()
            )
        ]

    def is_failed_or_pending_latest_purchase_after_expired_paid_subscriptions(
        self,
        db: Session,
        user_id: str,
        cutoff: datetime,
    ) -> bool:
        latest_sub = self.get_latest_any_by_user_id(db, user_id)
        if not latest_sub or latest_sub.payment_status not in ("failed", "pending"):
            return False

        paid_subscription_exists = (
            db.query(UserSubscription.id)
            .filter(
                UserSubscription.user_id == str(user_id),
                UserSubscription.payment_status == "paid",
            )
            .first()
            is not None
        )
        if not paid_subscription_exists:
            return False

        unexpired_paid_subscription_exists = (
            db.query(UserSubscription.id)
            .filter(
                UserSubscription.user_id == str(user_id),
                UserSubscription.payment_status == "paid",
                UserSubscription.expiry_at >= cutoff,
            )
            .first()
            is not None
        )

        return not unexpired_paid_subscription_exists

    def get_active_paid_credits(self, db: Session, user_id: str) -> List[UserSubscription]:
        return (
            db.query(UserSubscription)
            .filter(
                UserSubscription.user_id == str(user_id),
                UserSubscription.payment_status == "paid",
                UserSubscription.expiry_at >= datetime.utcnow(),
                UserSubscription.credits_left > 0,
            )
            .order_by(UserSubscription.expiry_at.asc())
            .all()
        )  
    def get_paginated_by_user_id(self, db: Session, user_id: str, skip: int, limit: int) -> tuple[List[UserSubscription], int]:
        query = db.query(UserSubscription).filter(UserSubscription.user_id == user_id)
        total = query.count()
        items = query.order_by(UserSubscription.purchase_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_active_by_user_id(self, db: Session, user_id: str) -> Optional[UserSubscription]:
        return db.query(UserSubscription).filter(
            UserSubscription.user_id == user_id,
            UserSubscription.expiry_at >= datetime.utcnow()
        ).first()

    def get_latest_by_user_id(self, db: Session, user_id: str) -> Optional[UserSubscription]:
        return db.query(UserSubscription).filter(
            UserSubscription.user_id == user_id,
            UserSubscription.payment_status == 'paid'
        ).order_by(UserSubscription.expiry_at.desc()).first()

    def get_latest_active_paid_by_user_id(self, db: Session, user_id: str) -> Optional[UserSubscription]:
        return db.query(UserSubscription).filter(
            UserSubscription.user_id == user_id,
            UserSubscription.payment_status == "paid",
            UserSubscription.expiry_at >= datetime.utcnow()
        ).order_by(UserSubscription.purchase_at.desc()).first()

    def get_by_purchase_id(self, db: Session, purchase_id: str) -> Optional[UserSubscription]:
        return db.query(UserSubscription).filter(UserSubscription.purchased_id == purchase_id).first()

    def get_by_id(self, db: Session, sub_id: UUID) -> Optional[UserSubscription]:
        return db.query(UserSubscription).filter(UserSubscription.id == sub_id).first()

    def get_with_plan(self, db: Session, sub_id: UUID) -> Optional[UserSubscription]:
        return db.query(UserSubscription).options(joinedload(UserSubscription.plan)).filter(UserSubscription.id == sub_id).first()
    
    def mark_paid(self, db: Session, sub: UserSubscription) -> UserSubscription:
        sub.payment_status = "paid"
        db.commit()
        db.refresh(sub)
        return sub
    
    def get_all_by_purchase_date(self, db: Session, purchase_date: date) -> List[UserSubscription]:
        return (
            db.query(UserSubscription)
            .filter(func.date(UserSubscription.purchase_at) == purchase_date)
            .order_by(UserSubscription.purchase_at.desc())
            .all()
        )

    def get_all_desc(self, db: Session) -> List[UserSubscription]:
        return db.query(UserSubscription).order_by(UserSubscription.purchase_at.desc()).all()

    def get_all_by_user_id_desc(self, db: Session, user_id: str) -> List[UserSubscription]:
        return (
            db.query(UserSubscription)
            .filter(UserSubscription.user_id == user_id)
            .order_by(UserSubscription.purchase_at.desc())
            .all()
        )

    def get_all_by_purchase_date(self, db: Session, purchase_date: date) -> List[UserSubscription]:
        return (
            db.query(UserSubscription)
            .filter(func.date(UserSubscription.purchase_at) == purchase_date)
            .order_by(UserSubscription.purchase_at.desc())
            .all()
        )
    
    def have_availed_free_plan(self, db: Session, user_id, plan_id) -> Optional[UserSubscription]:
        today = date.today() 
        now = datetime.utcnow()
        return (
            db.query(UserSubscription)
            .join(Plan)
            .filter(
                Plan.id == plan_id,
                Plan.pricing == Decimal("0.00"),
                UserSubscription.user_id == str(user_id),
                UserSubscription.expiry_at >= now,
                UserSubscription.payment_status == "paid",
            )
            .first()
        )
    
    def get_all_credits(self, db: Session, user_id) -> dict[str, int]:
        return  (
            db.query(UserSubscription)
            .filter(
                UserSubscription.user_id == str(user_id),
                UserSubscription.payment_status == "paid",
                # UserSubscription.amount_paid > Decimal("0.00"),
            )
            .all()
        )
    

    def get_all_credits_of_active_plan(self, db: Session, user_id) -> dict[str, int]:
        now = datetime.utcnow()

        return (
            db.query(UserSubscription)
            .filter(
                UserSubscription.user_id == str(user_id),
                UserSubscription.payment_status == "paid",
                extract('month', UserSubscription.purchase_at) == now.month,
                extract('year', UserSubscription.purchase_at) == now.year
            )
            .all()
        )
    
    def update_usage(self, db: Session, list) -> bool:
        for item in list:
            if item["type"] == "plan":
                    gen_credit = db.query(UserSubscription).filter(
                        UserSubscription.id == item["id"]
                    ).first()

                    if gen_credit:
                        gen_credit.credits_used += item["used_credit"]
                        gen_credit.credits_left -= item["used_credit"]

            else:
                credit_row = db.query(Users).filter(
                    Users.user_id == item["id"]
                ).first()

                if credit_row:
                        credit_row.general_credits_used += item["used_credit"]
                        credit_row.general_credits_left -= item["used_credit"]
        db.commit()

        return True
    
    def update(self, db: Session, plan: UserSubscription) -> UserSubscription:
        db.commit()
        db.refresh(plan)
        return plan
    
    def get_total_module_limit_for_month(self, db: Session, user_id: str, module_slug: str):
        plans = (
            db.query(PlanDetail)
            .join(Module, PlanDetail.module_id == Module.id)
            .join(Plan, PlanDetail.plan_id == Plan.id)
            .join(UserSubscription, UserSubscription.plan_id == Plan.id)
            .filter(
                UserSubscription.user_id == str(user_id),
                UserSubscription.payment_status == "paid",
                Module.slug == module_slug,
            )
            .all() 
        )
           
        limits = [p.module_limit for p in plans]

        if -1 in limits:
            return -1
        else:
            return max(limits) if limits else 0

class PlanDetailRepository:
    def create(self, db: Session, detail: PlanDetail) -> PlanDetail:
        db.add(detail)
        db.commit()
        db.refresh(detail)
        return detail

    def get_by_plan_id(self, db: Session, plan_id: int) -> List[PlanDetail]:
        return db.query(PlanDetail).filter(PlanDetail.plan_id == plan_id).all()
    def get_active_module_limit(
        self,
        db: Session,
        plan_id: int,
        module_id: int,
    ) -> Optional[PlanDetail]:
        return (
            db.query(PlanDetail)
            .filter(
                PlanDetail.plan_id == plan_id,
                PlanDetail.module_id == module_id,
                PlanDetail.module_limit.isnot(None),
                PlanDetail.module_limit != 0,
            )
            .first()
        )


plan_repository = PlanRepository()
module_repository = ModuleRepository()
user_subscription_repository = UserSubscriptionRepository()
plan_detail_repository = PlanDetailRepository()
