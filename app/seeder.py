"""Idempotently seed platform plans plus modules contributed by enabled domains."""

import importlib
import logging

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.subscription import Module, Plan, PlanDetail
from app.seeder_data import modules as platform_modules, plan_data

logger = logging.getLogger(__name__)


def _module_definitions() -> list[dict]:
    definitions = list(platform_modules)
    for domain in settings.enabled_domains:
        try:
            seed_module = importlib.import_module(f"app.api.seeds.{domain}")
        except ModuleNotFoundError as exc:
            if exc.name == f"app.api.seeds.{domain}":
                continue
            raise
        definitions.extend(getattr(seed_module, "MODULES", []))
    return definitions


def seed() -> None:
    with SessionLocal() as db:
        seeded_modules: list[Module] = []
        for data in _module_definitions():
            module = db.query(Module).filter(Module.slug == data["slug"]).one_or_none()
            if module is None:
                module = Module(**data)
                db.add(module)
                db.flush()
            seeded_modules.append(module)

        for data in plan_data:
            module_limit = data["module_limit"]
            values = {key: value for key, value in data.items() if key != "module_limit"}
            plan = db.query(Plan).filter(Plan.plan_title == values["plan_title"]).one_or_none()
            if plan is None:
                plan = Plan(**values)
                db.add(plan)
                db.flush()
            for module in seeded_modules:
                exists = db.query(PlanDetail).filter_by(plan_id=plan.id, module_id=module.id).one_or_none()
                if exists is None:
                    db.add(PlanDetail(plan_id=plan.id, module_id=module.id, module_limit=module_limit))
        db.commit()
        logger.info("Seeded %d modules and %d plans", len(seeded_modules), len(plan_data))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed()
