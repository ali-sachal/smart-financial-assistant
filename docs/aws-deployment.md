# AWS Quick Deployment

This page is the shortest path to a demo deployment. Use the full [DevOps runbook](devops-runbook.md) for secrets, smoke tests, monitoring, rollback, recovery, teardown, and troubleshooting.

## Prerequisites

AWS CLI v2, Docker, Python 3.11+, Node.js 20+, and AWS CDK v2 are required. Verify the intended account and region first:

```powershell
aws sts get-caller-identity
aws configure get region
docker version
cdk --version
```

## Deploy

```powershell
Set-Location infra
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cdk bootstrap
cdk diff `
  -c callback_url=smartfinance://auth/callback `
  -c logout_url=smartfinance://auth/logout `
  -c cognito_domain_prefix=my-unique-domain
cdk deploy `
  -c callback_url=smartfinance://auth/callback `
  -c logout_url=smartfinance://auth/logout `
  -c cognito_domain_prefix=my-unique-domain
```

The deployment outputs the API URL, Cognito pool/client/domain, table, bucket, secret ARN, log group, ECS cluster, and ECS service.

## Complete setup

1. Set the generated Secrets Manager value to the Gemini API key.
2. Force a new ECS deployment so tasks receive the secret.
3. Give the frontend engineer the API URL plus `/api`, Cognito domain/client/region, and exact callback/logout URLs.
4. Create the stable demo identity from the repository root:

   ```powershell
   $env:COGNITO_REGION = "<deployment-region>"
   $env:COGNITO_USER_POOL_ID = "<UserPoolId-output>"
   python -m scripts.create_demo_user --email demo@example.com
   ```

5. Sign in via Cognito PKCE and call `POST /api/demo/seed` once for the disposable demo user.
6. Run the authenticated smoke tests in the [DevOps runbook](devops-runbook.md).

The mobile client must send the Cognito **access token**, not the ID token. The demo stack exposes an HTTP ALB endpoint; add ACM-backed HTTPS before using real user data.
