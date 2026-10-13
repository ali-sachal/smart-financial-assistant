# Generic FastAPI SaaS Platform

This repository separates reusable platform services from product domains. It keeps authentication, PostgreSQL, users, subscriptions, credits, payments, invoices, notifications, Teams alerts, Kafka, S3, document generation, and optional AI integrations in the codebase while allowing each capability to be enabled independently.

## Status

The platform boot path is domain-neutral. Product modules are not imported by the application or Alembic unless enabled. `app/api/endpoints/example.py` demonstrates how a product adds routes without editing platform code.

The included billing engine is substantial, but production deployments still need provider credentials, verified payment webhooks, and infrastructure-specific monitoring. See `docs/enterprise-readiness.md`.

## Quick start

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m alembic -c app/alembic.ini upgrade head
python -m app.seeder
uvicorn app.main:app --reload --port 8080
```

Open `http://localhost:8080/docs`. For a local bearer token call `POST /api/auth/dev-token`. That endpoint is unavailable in production.

Docker:

```powershell
docker compose up --build
docker compose exec api python -m alembic -c app/alembic.ini upgrade head
docker compose exec api python -m app.seeder
```

Kafka remains optional. Start the bundled broker with `docker compose --profile events up`, then set `FEATURE_KAFKA=true`.

## Platform services

| Service | Flag | Default |
|---|---|---|
| JWT authentication | `FEATURE_AUTH` | on |
| User billing profiles | `FEATURE_USERS` | on |
| Plans, modules, credits, subscriptions | `FEATURE_SUBSCRIPTION` | on |
| Stripe/PayPal code | `FEATURE_PAYMENTS` / `FEATURE_PAYPAL` | Stripe on |
| PDF invoices | `FEATURE_INVOICES` | on |
| SMTP notifications | `FEATURE_EMAIL` | on |
| Kafka transport | `FEATURE_KAFKA` | off |
| S3 storage | `FEATURE_S3` | off |
| Teams exception alerts | `FEATURE_TEAMS` | off in `.env.example` |
| Gemini client | `FEATURE_LLM` | off |

Disabled integrations remain in the repository and do not initialize at startup. When Kafka is disabled, notification events use the SMTP handler directly; when SMTP is not configured they are logged and skipped.

## Add a product domain

Add the domain's modules under `app/api/`:

```text
app/api/
  endpoints/orders.py  # exports router, prefix, tags
  models/orders.py     # imports models based on app.db.base.Base
  seeds/orders.py      # exports MODULES
```

Enable it with:

```env
ENABLED_DOMAINS=orders
```

Example `api.py` metadata:

```python
router = APIRouter()
prefix = "/orders"
tags = ["Orders"]
```

Example paid module in `seed.py`:

```python
MODULES = [{
    "module_name": "Create order",
    "slug": "orders.create",
    "type": "credit",
    "credits_required": 1,
    "status": True,
}]
```

Use `subscription_service.ensure_paid_tool_access(db, user_id, "orders.create")` before metered work and `use_credit(...)` only after the operation succeeds.

## Multi-model AI

`ai.llms.gateway.llm_gateway` provides one interface for chat, async chat, streaming, structured output, tools, multimodal input, embeddings, images, retries, and configured fallbacks across LiteLLM-supported providers. Existing Gemini and NanoBanana clients remain available.

Define named profiles with `LLM_PROFILES_JSON`; values use LiteLLM model identifiers. Provider credentials stay in their standard environment variables and must never be included in the JSON profile.
See [`docs/ai-models.md`](docs/ai-models.md) for profile examples and the gateway API.

## Delivery automation

```powershell
python -m scripts.automation clean
python -m scripts.automation git --branch main --remote origin --dry-run
python -m scripts.automation vercel --dry-run
python -m scripts.automation vercel --prod
```

Git mode requires an existing repository and matching current branch. Vercel mode requires the CLI and an existing `.vercel/project.json` link. Neither command initializes or links external services automatically.

## Authentication modes

- `local`: verifies HS256 tokens issued by this API's development helper. Replace the secret in every deployed environment.
- `jwt_rs256` / `passport`: validates RS256 tokens and can enrich profiles through the configured Laravel API.
- `laravel`: requires the Laravel identity service.
- `none`: injects a synthetic development identity; never use this in production.

## Commands

```powershell
pytest -q
python -m compileall -q app
python -m alembic -c app/alembic.ini upgrade head
python -m app.seeder
```

Configuration is documented in `.env.example`. Secrets belong in environment variables or a secret manager, never in source control.
