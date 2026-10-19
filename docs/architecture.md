# Architecture

```text
Flutter + Cognito PKCE
        |
        | Cognito access token
        v
ALB -> FastAPI on ECS Fargate
          |-- Cognito JWKS verification
          |-- services/ business rules and forecast
          |-- repositories/ DynamoDB and S3 access
          `-- ai/ Gemini receipt and tool selection
                   |
                   `-- ai/agents -> allowlisted services only
```

## Package boundaries

- `app/api/endpoints`: request validation, authentication dependencies, service calls, and standardized responses only.
- `app/schemas`: every Pydantic HTTP, AI, and tool schema.
- `app/models`: plain DynamoDB entity dataclasses and enums.
- `app/repositories`: all boto3 DynamoDB/S3 operations.
- `app/services`: all finance rules, calculations, orchestration, and audit construction.
- `ai`: Gemini provider boundary and structured receipt extraction.
- `ai/agents`: tool declarations, validation, dispatch, grounding, and safety limits.
- `infra`: AWS CDK deployment.

## DynamoDB access patterns

The base partition is `PK=USER#{cognito_sub}`. Entity IDs form the sort key. Transaction and bill timelines use overloaded `GSI1` keys. Conversations and audits use sort-key prefixes. Product repositories never scan the table.

Receipt bytes are private S3 objects at `users/{sub}/receipts/{receipt_id}.{extension}`. DynamoDB stores only the key, digest, extraction, confidence state, and linked transaction ID.

## Trust boundaries

Only a validated Cognito access token creates identity context. Request bodies and model calls cannot supply a user ID. Gemini can select only declared tools; tool arguments pass through Pydantic validation and the registry injects the authenticated identity.
