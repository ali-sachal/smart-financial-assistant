from datetime import date, timedelta

from ai.agents.tools import finance_tool_registry
from app.repositories.finance import finance_repository
from app.schemas.finance import BudgetUpsert, TransactionCreate
from app.services.finance_service import finance_service


def test_user_partitions_are_isolated():
    finance_service.seed_demo("alpha")
    finance_service.seed_demo("beta")
    finance_service.create_transaction(
        "alpha",
        TransactionCreate(
            amount_minor=1234,
            transaction_type="expense",
            category="testing",
            merchant="Alpha only",
            posted_at=date.today(),
        ),
    )
    alpha = finance_service.list_transactions("alpha", date.today() - timedelta(days=1), date.today())["items"]
    beta = finance_service.list_transactions("beta", date.today() - timedelta(days=1), date.today())["items"]
    assert any(item["merchant"] == "Alpha only" for item in alpha)
    assert not any(item["merchant"] == "Alpha only" for item in beta)


def test_budget_math_and_agent_write_audit():
    user_id = "budget-user"
    finance_service.seed_demo(user_id)
    month = date.today().strftime("%Y-%m")
    result = finance_service.upsert_budget(
        user_id, month, "dining", BudgetUpsert(limit_minor=20_000), actor="agent"
    )
    assert result["items"][0]["limit_minor"] == 20_000
    audits, _ = finance_repository.query_prefix(user_id, "AUDIT#")
    assert audits[-1]["action"] == "budget.upsert"
    assert audits[-1]["actor"] == "agent"


def test_forecast_is_deterministic_and_has_confidence_band():
    user_id = "forecast-user"
    finance_service.seed_demo(user_id)
    first = finance_service.forecast(user_id, 30)
    second = finance_service.forecast(user_id, 30)
    assert first == second
    assert len(first["points"]) == 30
    assert first["confidence"] == 0.80
    assert all(point["lower_minor"] <= point["projected_minor"] <= point["upper_minor"] for point in first["points"])


def test_agent_rejects_identity_injection():
    finance_service.seed_demo("safe-user")
    try:
        finance_tool_registry.execute("safe-user", "fetch_balance", {"user_id": "victim"})
    except Exception as exc:
        assert getattr(exc, "error_code", None) == "FIN_UNSAFE_ACTION"
    else:
        raise AssertionError("identity injection was accepted")
