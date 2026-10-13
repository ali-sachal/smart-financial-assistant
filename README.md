# Smart Personal Finance Assistant

FastAPI backend for authenticated personal-finance dashboards, budgeting, bill tracking, receipt extraction, explainable cash-flow forecasts, and a grounded Gemini tool-calling assistant.

## Core behavior

- Amazon Cognito access tokens identify users by immutable `sub`.
- DynamoDB stores user-partitioned finance entities; S3 stores private receipt objects.
- All money is represented as integer minor units.
- Gemini extracts receipts and selects allowlisted tools, while services perform all calculations and writes.
- Agent writes are limited to reversible records and produce immutable audit items.
- Every API result uses a stable code/message envelope and request ID.

## Local development

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

Local configuration defaults to the in-memory repository. Protected endpoints still require Cognito; in automated tests the verifier dependency is replaced with a test identity. Configure `COGNITO_REGION`, `COGNITO_USER_POOL_ID`, and `COGNITO_APP_CLIENT_ID` to use a real development User Pool.

Open `http://localhost:8080/docs`. The only unauthenticated product endpoint is `GET /api/health/check`.

## Verification

```powershell
python -m compileall -q app ai scripts
python -m pytest -q
```

## AWS deployment

The CDK stack builds the container and provisions Cognito, DynamoDB, S3, ECS Fargate, an ALB, Secrets Manager, IAM, and CloudWatch.

```powershell
cd infra
pip install -r requirements.txt
cdk bootstrap
cdk deploy -c cognito_domain_prefix=my-unique-prefix
```

After deployment, set the Gemini secret value and create the stable demo identity without placing its password in command history:

```powershell
python -m scripts.create_demo_user --email demo@example.com
```

## Documentation

| Audience | Document |
|---|---|
| Flutter engineer | [Frontend integration guide](docs/frontend-integration.md) |
| Flutter and backend engineers | [API reference](docs/api-reference.md) |
| DevOps/SRE | [Deployment and operations runbook](docs/devops-runbook.md) |
| First deployment | [AWS quick deployment](docs/aws-deployment.md) |
| All engineers | [Architecture](docs/architecture.md) |
| Backend/AI reviewers | [Core algorithms](docs/core-algorithms.md) |

The frontend handoff covers Cognito PKCE, secure token use, API-client behavior, cache invalidation, screen flows, and acceptance checks. The DevOps handoff covers configuration, CDK outputs, secret rotation, demo provisioning, logs, monitoring, release/rollback, recovery, teardown, and production hardening.
