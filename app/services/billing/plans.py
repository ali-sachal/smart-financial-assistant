from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import AppException, Message, ResponseCode
from app.models.subscription import Module, Plan, PlanDetail
from app.repositories.subscription import module_repository, plan_detail_repository, plan_repository
from app.schemas.subscription import ModuleCreate, ModuleUpdate, PlanCreate, PlanModuleDetail, PlanWithModules


class PlanService:
    def list(self, db: Session, active_plan_id: Optional[int] = None) -> list[PlanWithModules]:
        result = []
        for plan in plan_repository.get_all(db):
            modules = [
                PlanModuleDetail(
                    module_id=detail.module.id,
                    module_slug=detail.module.slug,
                    module_name=detail.module.module_name,
                    module_type=detail.module.type,
                    module_limit=detail.module_limit,
                )
                for detail in plan.details if detail.module
            ]
            result.append(PlanWithModules(
                id=plan.id, plan_title=plan.plan_title, pricing=plan.pricing,
                duration=plan.duration, status=plan.status, credits=plan.credits,
                created_at=plan.created_at, last_updated=plan.last_updated,
                modules=modules, subscribed=plan.id == active_plan_id,
            ))
        return result

    def get(self, db: Session, plan_id: int) -> Plan:
        plan = plan_repository.get_by_id(db, plan_id)
        if not plan:
            raise AppException(ResponseCode.NOT_FOUND, Message.RESOURCE_NOT_FOUND, {"resource": "Plan", "id": plan_id})
        return plan

    def create(self, db: Session, payload: PlanCreate) -> Plan:
        plan = plan_repository.create(db, Plan(**payload.model_dump(exclude={"modules"})))
        for item in payload.modules:
            module = module_repository.get_by_slug(db, item.module_slug)
            if not module:
                raise AppException(ResponseCode.NOT_FOUND, Message.RESOURCE_NOT_FOUND, {"module": item.module_slug})
            plan_detail_repository.create(db, PlanDetail(
                plan_id=plan.id, module_id=module.id, module_limit=item.module_limit
            ))
        return plan

    def create_module(self, db: Session, payload: ModuleCreate) -> Module:
        return module_repository.create(db, Module(**payload.model_dump()))

    def list_modules(self, db: Session) -> list[Module]:
        return module_repository.get_all(db)

    def update_module(self, db: Session, module_id: int, payload: ModuleUpdate) -> Module:
        module = module_repository.get_by_id(db, module_id)
        if not module:
            raise AppException(ResponseCode.NOT_FOUND, Message.RESOURCE_NOT_FOUND, {"module_id": module_id})
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(module, key, value)
        return module_repository.update(db, module)
