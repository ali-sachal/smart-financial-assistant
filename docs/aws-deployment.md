# AWS Deployment

## Resources

The CDK stack creates:

- Cognito User Pool, Managed Login domain, and public Flutter app client using authorization code with PKCE.
- On-demand encrypted DynamoDB table with point-in-time recovery and `GSI1`.
- Private, encrypted, versioned receipt bucket.
- Fargate task and service behind a public ALB.
- ECR-backed Docker image asset.
- Secrets Manager secret for Gemini.
- Separate ECS execution/task roles and least-privilege table/bucket grants.
- CloudWatch logs, CPU and ALB 5xx alarms, and an operations dashboard.

## Deploy

```powershell
cd infra
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cdk bootstrap
cdk deploy `
  -c callback_url=smartfinance://auth/callback `
  -c logout_url=smartfinance://auth/logout `
  -c cognito_domain_prefix=my-unique-domain
```

Set the generated Gemini secret value after the first deployment. Secrets are injected at task start; force a new ECS deployment after rotating them.

## Flutter authentication contract

Use the output User Pool ID, client ID, region, domain, callback URL, and logout URL. Request the `openid`, `email`, and `profile` scopes with authorization-code PKCE. Send the access token—not the ID token—as `Authorization: Bearer ...`.

The API validates RS256 signature, Cognito issuer, expiration, `token_use=access`, and `client_id`. The access-token `sub` is the sole DynamoDB user identifier.

## Demo setup

Run `python -m scripts.create_demo_user --email demo@example.com` with AWS operator credentials. The script reads the password interactively, suppresses Cognito email delivery, confirms the email attribute, and never logs the password. After login, call `POST /api/demo/seed` once with the user's access token.
