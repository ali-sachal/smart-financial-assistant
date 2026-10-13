# Core Algorithm Description

## Intent routing and tool execution

The agent receives a system policy, the user's current message, and strict Gemini function declarations. It does not receive database credentials or raw repository access. The backend inspects each function call, rejects unknown tools and identity fields, validates arguments with the tool's Pydantic schema, then invokes the mapped finance service with the authenticated Cognito `sub`.

Tool output is serialized back into the next model turn. This repeats for at most five rounds. Numerical answers must therefore be based on a recorded tool result. Budget, bill, and category changes are reversible and are atomically paired with an audit item. No tool exists for payments, transfers, deletion, or bulk mutation.

When Gemini is not configured, the demo fallback recognizes the two judged flows—affordability and budget updates—and invokes the same validated tool registry. It does not fabricate account values.

## Receipt parsing

The receipt service validates a 10 MB limit and verifies JPEG, PNG, or PDF magic bytes against the declared media type. A SHA-256 digest prevents duplicate ingestion. The private object is written to S3 and Gemini receives an extraction-only prompt plus a Pydantic response schema.

The structured result contains merchant, date, subtotal, tax, total, currency, category, line items, and confidence. A transaction is created automatically only when merchant, date, and positive total are present and confidence is at least `0.80`; otherwise the receipt enters `needs_review`. Printed receipt text is always treated as data, never as agent instruction.

## Cash-flow forecast

For forecast day `t`:

```text
projected[t] = projected[t-1]
             + scheduled_income[t]
             - scheduled_bills[t]
             - mean_historical_discretionary_daily_spend
```

The discretionary baseline uses the prior 60 days and excludes income, transfers, refunds, and transactions explicitly sourced as bills. The 80% band is:

```text
lower[t] = projected[t] - 1.2816 * daily_spend_stddev * sqrt(t)
upper[t] = projected[t] + 1.2816 * daily_spend_stddev * sqrt(t)
```

The first lower-bound crossing below zero creates a negative-balance warning. A crossing below the user's configured buffer creates a safety-buffer warning. The API returns all daily inputs and bands so the model and user can explain the recommendation.
