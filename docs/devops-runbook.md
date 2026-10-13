# DevOps Deployment and Operations Runbook

This is the operator handoff for deploying and running the backend on AWS. The stack is designed for a hackathon/demo environment; the production-hardening gaps are called out explicitly.

## 1. Provisioned architecture

The `infra` CDK stack creates:

- Cognito User Pool, Managed Login domain, and public PKCE app client.
- One on-demand, encrypted DynamoDB table with `GSI1` and point-in-time recovery.
- One private, encrypted, versioned S3 receipt bucket.
- Docker image asset and ECR repository managed by CDK assets.
- ECS Fargate service behind an Application Load Balancer.
- Secrets Manager secret for the Gemini API key.
- Separate ECS execution and task IAM roles.
- CloudWatch log group, Container Insights, dashboard, CPU alarm, and ALB 5xx alarm.

The Fargate task receives no static AWS credentials. Its task role can access only the finance table and receipt bucket. Its execution role can retrieve the Gemini secret while starting the container.

## 2. Prerequisites

- AWS account and an operator role permitted to bootstrap/deploy CDK.
- AWS CLI v2 authenticated to the target account.
- Docker Desktop/Engine running.
- Python 3.11 or newer.
- Node.js 20 or newer and AWS CDK v2 (`npm install -g aws-cdk`).

Verify the deployment identity and region before every deployment:

```powershell
aws sts get-caller-identity
aws configure get region
cdk --version
docker version
```

Use separate AWS accounts where possible. At minimum, use unique Cognito domain prefixes and stack names for independent environments.

## 3. Configuration inventory

Application configuration is defined in `.env.example` and `app/core/config.py`.

| Variable | Local | AWS deployment | Sensitive |
|---|---|---|---|
| `ENVIRONMENT` | `local` | Set to `production` by CDK | No |
| `API_PREFIX` | `/api` | `/api` default | No |
| `APP_NAME`, `APP_TAGLINE`, `APP_VERSION` | Optional display metadata | Application defaults | No |
| `API_PREFIX` | `/api` | `/api` default | No |
| `CORS_ORIGINS`, `CORS_ALLOW_CREDENTIALS` | Local client origins | Set explicit deployed web origins if used | No |
| `LOG_LEVEL`, `LOG_JSON`, `LOGS_DIR` | Optional | JSON stdout configured | No |
| `USE_IN_MEMORY_REPOSITORY` | `true` default | `false` | No |
| `AWS_REGION` | Required for real AWS services | Injected by CDK | No |
| `FINANCE_TABLE_NAME` | Required for DynamoDB mode | Injected by CDK | No |
| `DYNAMODB_ENDPOINT_URL` | Optional local emulator endpoint | Empty | No |
| `RECEIPTS_BUCKET_NAME` | Required for receipt storage | Injected by CDK | No |
| `RECEIPT_MAX_BYTES`, `RECEIPT_AUTO_CREATE_CONFIDENCE` | Optional behavior overrides | Application defaults | No |
| `COGNITO_REGION` | Required for real authentication | Injected by CDK | No |
| `COGNITO_USER_POOL_ID` | Required for real authentication | Injected by CDK | No |
| `COGNITO_APP_CLIENT_ID` | Required for real authentication | Injected by CDK | No |
| `COGNITO_JWKS_TTL_SECONDS`, `CLOCK_SKEW_LEEWAY` | Optional verification tuning | Application defaults | No |
| `GEMINI_API_KEY` | Required for AI features | Injected from Secrets Manager | **Yes** |
| `GEMINI_MODEL_NAME` | Optional model override | Application default | No |
| `AGENT_MAX_TOOL_ROUNDS` | Optional safety limit | Application default (`5`) | No |

Do not commit `.env`, tokens, passwords, AWS credentials, or secret exports. Local log files may contain identifiers and should not be committed or shipped outside approved storage.

## 4. Local run

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

The in-memory repository is suitable for development but is reset when the process restarts. Protected routes still require a valid Cognito access token. Automated tests substitute a fake verifier; production authentication is never weakened.

Verify liveness:

```powershell
Invoke-RestMethod http://localhost:8080/api/health/check
```

Container parity:

```powershell
docker compose up --build
```

## 5. Deploy with CDK

From the repository root:

```powershell
Set-Location infra
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cdk bootstrap
cdk synth `
  -c callback_url=smartfinance://auth/callback `
  -c logout_url=smartfinance://auth/logout `
  -c cognito_domain_prefix=my-unique-domain
cdk diff `
  -c callback_url=smartfinance://auth/callback `
  -c logout_url=smartfinance://auth/logout `
  -c cognito_domain_prefix=my-unique-domain
cdk deploy `
  -c callback_url=smartfinance://auth/callback `
  -c logout_url=smartfinance://auth/logout `
  -c cognito_domain_prefix=my-unique-domain
```

The Cognito domain prefix is globally constrained within its AWS region and must be unique. Callback and logout URLs must exactly match the Flutter configuration. Review `cdk diff` for IAM or data-resource replacements before approving deployment.

The CloudFormation stack name is `SmartFinanceAssistant`. Capture its outputs:

```powershell
$stackName = "SmartFinanceAssistant"
$outputs = aws cloudformation describe-stacks `
  --stack-name $stackName `
  --query "Stacks[0].Outputs" | ConvertFrom-Json
$outputs | Sort-Object OutputKey | Format-Table OutputKey,OutputValue
```

Provide `ApiUrl` plus `/api`, `CognitoDomain`, `UserPoolClientId`, the deployed region, and the configured callback/logout URLs to the frontend engineer. Treat other outputs as operator data.

## 6. Set or rotate the Gemini secret

The first deployment creates a Secrets Manager resource with a generated placeholder value. Replace it through the AWS Console where possible. For CLI automation, write the key to a temporary access-controlled file rather than putting it directly into shell history:

```powershell
$secretArn = ($outputs | Where-Object OutputKey -eq "GeminiSecretArn").OutputValue
aws secretsmanager put-secret-value `
  --secret-id $secretArn `
  --secret-string file://C:/secure-temp/gemini-key.txt
```

Delete the temporary file using the organization's secure-secret procedure. A running ECS task does not automatically reload injected secrets. Force a new deployment after setting or rotating the value:

```powershell
$clusterName = ($outputs | Where-Object OutputKey -eq "EcsClusterName").OutputValue
$serviceName = ($outputs | Where-Object OutputKey -eq "EcsServiceName").OutputValue
aws ecs update-service `
  --cluster $clusterName `
  --service $serviceName `
  --force-new-deployment
aws ecs wait services-stable --cluster $clusterName --services $serviceName
```

Never print the secret, include it in task environment output, or add it to CloudFormation/CDK context.

## 7. Create the demo identity

Run the script with an operator identity allowed to administer users in this specific pool. It prompts for the password without echoing or logging it.

```powershell
Set-Location ..
$env:COGNITO_REGION = (aws configure get region)
$env:COGNITO_USER_POOL_ID = ($outputs | Where-Object OutputKey -eq "UserPoolId").OutputValue
python -m scripts.create_demo_user --email demo@example.com
```

After the user signs in through Cognito, call `POST /api/demo/seed` with that user's access token. Seeding is destructive for that authenticated user's finance partition and must be used only for a disposable demo identity.

## 8. Deployment smoke test

First check the unauthenticated route:

```powershell
$apiUrl = ($outputs | Where-Object OutputKey -eq "ApiUrl").OutputValue
Invoke-RestMethod "$apiUrl/api/health/check"
```

Obtain an **access token** through the same Cognito PKCE login used by Flutter. Do not paste it into issue trackers or CI output. For an interactive shell:

```powershell
$headers = @{
  Authorization = "Bearer $env:ACCESS_TOKEN"
  "X-Request-ID" = [guid]::NewGuid().ToString()
}
Invoke-RestMethod "$apiUrl/api/auth/me" -Headers $headers
Invoke-RestMethod "$apiUrl/api/accounts" -Headers $headers
Invoke-RestMethod "$apiUrl/api/dashboard?month=$((Get-Date).ToString('yyyy-MM'))" -Headers $headers
Invoke-RestMethod "$apiUrl/api/forecast?days=30" -Headers $headers
```

For a disposable demo account, seed before the last three reads. Also smoke-test one receipt upload and one chat prompt after the Gemini secret is configured. Confirm the same request ID is visible in the response and CloudWatch logs.

## 9. Logs and tracing

The application writes date-based local files under `logs/{component}/YYYY-MM-DD.log` and equivalent structured JSON to stdout. Fargate storage is ephemeral; CloudWatch is the durable source of truth.

Components are `api`, `services`, `repositories`, `auth`, `ai`, `agent`, `audit`, and `errors`. Records can include request ID, Cognito `sub`, route, operation, entity ID, latency, status, application error code, model metadata, and AWS request ID. Redaction removes bearer tokens, passwords, authorization codes, receipt content, and known secrets.

Tail the deployed log group:

```powershell
$logGroup = ($outputs | Where-Object OutputKey -eq "ApiLogGroupName").OutputValue
aws logs tail $logGroup --since 10m --follow
```

Start an investigation with `request_id`, then correlate the application error code and AWS request ID. Restrict log access because user identifiers and financial entity metadata remain sensitive even after secret redaction.

## 10. Monitoring and alarms

The stack creates:

- ECS CPU alarm: over 80%, 2 of 3 evaluation periods.
- ALB 5xx alarm: at least 5 errors across 2 evaluation periods.
- Container Insights for task-level metrics.
- An operations dashboard with API CPU.

After deployment, attach alarm actions to the team's SNS/PagerDuty destination; the stack does not choose a notification target. Add alarms for target response time, healthy host count, task restarts, memory, DynamoDB throttles/system errors, and S3 5xx for a production environment.

`/api/health/check` is liveness only. It does not prove DynamoDB, S3, Cognito JWKS, or Gemini availability. Use the authenticated smoke test as readiness/integration verification.

## 11. IAM, data protection, and retention

- DynamoDB uses AWS-managed encryption, on-demand billing, PITR, and `RemovalPolicy.RETAIN`.
- S3 blocks all public access, enforces TLS, enables versioning/encryption, and uses `RemovalPolicy.RETAIN`.
- Cognito User Pool is retained on stack deletion.
- The CloudWatch application log group currently retains one month and is destroyed with the stack.
- Product repositories query the authenticated user's partition; they do not scan the table.
- The receipt bucket is never exposed directly to the mobile app.

Review retention against organizational policy. For stronger isolation, use customer-managed KMS keys and explicit key policies. Enable CloudTrail data events only after evaluating cost and sensitivity.

## 12. Release and rollback

Before release:

```powershell
python -m compileall -q app ai scripts infra
python -m pytest -q
Set-Location infra
cdk synth -c cognito_domain_prefix=my-unique-domain
cdk diff -c cognito_domain_prefix=my-unique-domain
```

Deploy from a tagged commit and record the commit SHA, CloudFormation change set, image digest, operator, and smoke-test request IDs. CDK publishes a new immutable image asset and ECS replaces tasks while the ALB health check protects traffic.

To roll back application code, check out the previously approved tag and run `cdk diff` and `cdk deploy` with the same context values. Do not roll back data by deleting the table or bucket. If a release changes item shape or access patterns, maintain backward compatibility until rollback is no longer required.

For data recovery, use DynamoDB PITR to restore to a new table, validate it, and deploy a controlled configuration change. Restore S3 objects from versions rather than deleting the bucket. Both operations require an incident-specific plan and approval.

## 13. Teardown

```powershell
Set-Location infra
cdk destroy -c cognito_domain_prefix=my-unique-domain
```

Destroying the stack does **not** remove retained DynamoDB, S3, or Cognito resources. Inventory retained resources and backups before manual cleanup. Deletion is irreversible and should follow the account's approval and retention process.

## 14. Troubleshooting

| Symptom | Checks and likely resolution |
|---|---|
| Cognito domain creation fails | Choose a different region-unique `cognito_domain_prefix`. |
| Callback returns an OAuth error | Compare callback URL, logout URL, client ID, scopes, and PKCE S256 values character for character. |
| API returns `AUTH_TOKEN_TYPE_INVALID` | Flutter sent an ID token; send the Cognito access token. |
| API returns issuer/client/unknown-key auth errors | Confirm region, pool, and client outputs; inspect JWKS reachability and task egress. Do not weaken validation. |
| ALB target remains unhealthy | Inspect stopped-task reason and logs; confirm port 8000 and `/api/health/check`; verify image startup. |
| Task cannot start | Check ECS events, execution-role secret access, image pull, and whether the Gemini secret has a usable value. |
| DynamoDB requests fail | Confirm `FINANCE_TABLE_NAME`, task-role grants, region, table status, and CloudWatch/AWS request ID. |
| Receipt upload returns service unavailable | Check bucket output, task-role S3 permissions, file limits, Gemini secret/model access, and AI logs. |
| Chat fails while dashboard works | Gemini is isolated from deterministic finance APIs; inspect AI/agent logs and quota without restarting unrelated services. |
| No logs appear | Confirm task is running, output log group is correct, and execution role can create/write log streams. |
| Browser/mobile blocks API request | For Flutter web, configure explicit CORS origins in the API. Native Flutter is not subject to browser CORS. |

## 15. Production hardening before real users

The current stack is demo-oriented. Before production:

- Terminate HTTPS at the ALB with ACM and Route 53; redirect HTTP to HTTPS. The current `ApiUrl` is HTTP.
- Move tasks to private subnets with controlled NAT or VPC endpoints. They currently receive public IPs.
- Add AWS WAF, rate limits, autoscaling, multi-environment pipelines, and alarm notifications.
- Restrict or disable `/api/demo/seed` outside disposable demo environments.
- Use explicit CORS origins if a web frontend is introduced.
- Add readiness checks, disaster-recovery exercises, secret rotation, dependency scanning, and image scanning gates.
- Review Cognito MFA, threat protection, password policy, account recovery, and token lifetimes.
- Establish financial-data retention, deletion, privacy, incident-response, and audit-access policies.
