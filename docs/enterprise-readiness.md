# Enterprise readiness

## Included baseline

- Request IDs and response timing
- Structured logging and SQL query timing
- Consistent error envelopes
- PostgreSQL health check
- JWT validation and admin dependencies
- Feature-gated integrations and lifecycle hooks
- Initial Alembic schema and idempotent domain-aware seeding
- Plans, modules, entitlements, credits, purchase history, and invoices
- Stripe, PayPal, SMTP, Teams webhook, Kafka, and the preserved S3 implementation

## Required before production

1. Persist Stripe webhook event IDs for durable idempotency and add equivalent signed PayPal webhook handling. A browser redirect must never be the payment authority.
2. Add payment-event, invoice, refund, notification-delivery, and audit tables.
3. Use a transactional outbox for messages; configure retries and a dead-letter queue.
4. Select a production identity provider and implement the required registration, recovery, MFA, and revocation lifecycle there.
5. Add rate limiting, authorization policies, tenant boundaries where needed, and secret-manager integration.
6. Export metrics and traces to the deployment's observability stack and define alerts/SLOs.
7. Add PostgreSQL integration, migration, provider-contract, webhook, and end-to-end tests.
8. Run dependency, container, static-analysis, and secret scanning in CI.

Feature flags control availability; they are not authorization. Sensitive endpoints must continue to use authentication and role dependencies.
