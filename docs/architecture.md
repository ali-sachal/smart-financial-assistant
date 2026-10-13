# Architecture

```text
app/
  api/
    endpoints/         platform and product HTTP APIs
    models/            optional product model-registration modules
    seeds/             optional product billing-module definitions
  core/                config, auth, errors, middleware, domain discovery
  db/                  SQLAlchemy engine and declarative base
  models/              platform users and billing models
  repositories/        persistence operations
  services/            billing, payments, health, and provider services
  invoices/            generic invoice renderer
  kafka/               event transport and local notification fallback
  utils/               logging, email, storage, and document helpers
  alembic/              platform migrations
tests/                  platform boot and authentication tests
```

Platform code never imports a product domain by name. `ENABLED_DOMAINS` selects domain packages at startup and during Alembic metadata discovery.
