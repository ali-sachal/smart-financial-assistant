"""Domain-neutral defaults. Product modules are loaded from app/api/seeds/*.py."""

modules = []

plan_data = [
    {
        "plan_title": "Starter",
        "pricing": 0,
        "duration": 30,
        "credits": 25,
        "status": True,
        "module_limit": 5,
    },
    {
        "plan_title": "Professional",
        "pricing": 29,
        "duration": 30,
        "credits": 500,
        "status": True,
        "module_limit": 100,
    },
]
