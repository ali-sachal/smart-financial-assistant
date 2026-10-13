# Frontend Integration Guide (Flutter)

This guide is the frontend handoff for authentication, API consumption, state management, and the demo journey. Field-level request and response examples are in the [API reference](api-reference.md).

## 1. Values required from DevOps

Configure these values per environment; do not hard-code production values in source control.

| Value | Example | Purpose |
|---|---|---|
| `apiBaseUrl` | `https://api.example.com/api` | Finance API base URL |
| `cognitoDomain` | `https://my-domain.auth.us-east-1.amazoncognito.com` | Cognito Managed Login host |
| `cognitoClientId` | `abc123...` | Public mobile app client ID |
| `cognitoCallbackUrl` | `smartfinance://auth/callback` | Deep link registered in Cognito and Flutter |
| `cognitoLogoutUrl` | `smartfinance://auth/logout` | Post-logout deep link |
| `cognitoScopes` | `openid email profile` | OAuth scopes |

The mobile client is public and must not have or request a client secret. `apiBaseUrl` must include `/api`.

## 2. Cognito authorization-code flow with PKCE

Use a maintained OAuth/OIDC package such as `flutter_appauth`, or implement the equivalent flow below.

1. Generate a cryptographically random `state` and PKCE `code_verifier`.
2. Calculate `code_challenge = BASE64URL(SHA256(code_verifier))` without padding.
3. Open the system browser at `{cognitoDomain}/oauth2/authorize` with:
   - `client_id={cognitoClientId}`
   - `response_type=code`
   - `redirect_uri={cognitoCallbackUrl}`
   - `scope=openid email profile`
   - `state={state}`
   - `code_challenge={code_challenge}`
   - `code_challenge_method=S256`
4. Handle the callback deep link, reject it if `state` does not exactly match, and read `code`.
5. Exchange the code at `{cognitoDomain}/oauth2/token` using form-encoded fields:
   - `grant_type=authorization_code`
   - `client_id={cognitoClientId}`
   - `code={code}`
   - `redirect_uri={cognitoCallbackUrl}`
   - `code_verifier={code_verifier}`
6. Store tokens in platform secure storage, never SharedPreferences.

Use the **access token** as `Authorization: Bearer <access_token>` for the API. The ID token is only for optional local display data and must not be sent as the API bearer token. Never parse a JWT and treat its claims as authorization; the backend is authoritative.

Refresh at `{cognitoDomain}/oauth2/token` with `grant_type=refresh_token`, `client_id`, and `refresh_token`. Use a single-flight refresh so concurrent `401` responses do not start multiple refreshes. Retry the original request once after a successful refresh, then sign the user out if it still receives `401`.

To log out, clear secure local tokens and open:

```text
{cognitoDomain}/logout?client_id={cognitoClientId}&logout_uri={urlEncodedLogoutUrl}
```

Register callback and logout schemes for both Android and iOS. The strings must exactly match the CDK deployment parameters, including case and trailing slashes.

## 3. API client contract

Send these headers:

```http
Authorization: Bearer <Cognito access token>
Accept: application/json
Content-Type: application/json
X-Request-ID: <new UUID per logical request>
```

For receipt upload, use `multipart/form-data` with a single field named `file`; let the HTTP library set its boundary. The response echoes `X-Request-ID` and includes the same value in the JSON envelope. Include this ID in support/debug reports.

All JSON endpoints return one envelope:

```dart
class ApiEnvelope<T> {
  const ApiEnvelope({
    required this.success,
    required this.code,
    required this.message,
    required this.result,
    required this.errors,
    required this.requestId,
  });

  final bool success;
  final String code;
  final String message;
  final T? result;
  final Object? errors;
  final String requestId;
}
```

Do not decide success from the message text. Require an HTTP `2xx` and `success == true`; branch on the stable `code` for expected failures. Preserve `errors` for validation UI and diagnostics, but do not display raw internal details as the primary user message.

Recommended timeouts:

- Normal reads and writes: 15 seconds.
- Chat: 45 seconds.
- Receipt scan: 60 seconds, with upload progress.

Retry one transient `429`, `502`, `503`, or `504` response with jitter only when the operation is safe. `GET` requests are safe to retry. Do not blindly retry `POST /transactions`, `POST /bills`, `POST /receipts/scan`, `POST /chat`, or `POST /demo/seed`, because a timed-out request may already have completed.

## 4. Money, dates, and identity

- Money is always an integer in minor units: `$12.34` is `1234`. Never use floating-point arithmetic for totals.
- Format money using the user's profile currency. For the MVP, one user uses one ISO-4217 currency.
- Calendar dates use `YYYY-MM-DD`; budget months use `YYYY-MM`.
- Timestamps are UTC ISO-8601 strings. Convert them for display using the profile timezone.
- Transaction `amount_minor` is non-negative. `type` (`expense`, `income`, `transfer`, or `refund`) defines direction.
- IDs and pagination cursors are opaque strings; never derive or modify them.
- Never send a `user_id`. The backend derives identity exclusively from the token's Cognito `sub`.

## 5. Suggested Flutter boundaries

Keep transport models separate from view state. A practical Riverpod layout is:

```text
authController       -> login, token refresh, logout
profileRepository    -> /auth/me and /profile
financeRepository    -> accounts, transactions, budgets, bills
dashboardRepository  -> dashboard and forecast
receiptRepository    -> upload and correction
assistantRepository  -> chat and conversation history
```

After a successful mutation, invalidate only affected providers:

| Mutation | Invalidate/refetch |
|---|---|
| Profile update | Profile, dashboard |
| Transaction create/update | Transactions, dashboard, forecast, relevant budget |
| Budget update | Budget, dashboard, forecast |
| Bill create/update | Bills, dashboard, forecast |
| Receipt transaction creation/correction | Receipt, transactions, dashboard, forecast |
| Agent write | Use `tool_results` to identify writes, then refresh dashboard plus affected entity data |
| Demo seed | All authenticated finance state |

Treat chat text as untrusted display content. Render it as plain text or sanitized Markdown; never execute links, HTML, scripts, or model-provided commands.

## 6. Screen and user journey

### App launch and sign-in

1. Restore tokens from secure storage.
2. If the access token is expired, attempt one refresh.
3. Call `GET /auth/me` to validate the session.
4. Call `GET /profile`.
5. If profile returns `404`, show onboarding and submit `PUT /profile`.
6. Otherwise open the dashboard.

Do not infer a missing profile from a network error. Only the stable not-found response should enter onboarding.

### Demo initialization

Expose `POST /demo/seed` only in the demo/admin UI. It deletes and replaces all finance data for the currently authenticated user. Require an explicit confirmation and explain that the action cannot be undone through the app.

### Dashboard

Use `GET /dashboard?month=YYYY-MM` as the main screen aggregate. It already contains balances, income, spending, category totals, budget utilization, upcoming bills, and insights. Fetch `GET /forecast?days=30` only when the forecast card or detail screen needs daily points.

### Transactions

Use the returned cursor unchanged for the next page. Keep filter values stable while paginating; a filter change starts again without a cursor. After editing a category, replace the visible item immediately from the mutation result, then refresh dependent totals.

### Budgets and bills

Budget identity is `{month, category}` and the route uses both values. Bill identity is the opaque `bill_id`. Use server-returned records after writes rather than constructing local versions.

### Receipt scan

1. Accept JPEG, PNG, or PDF up to 10 MiB.
2. Show upload progress and keep the screen alive during extraction.
3. If status is `parsed`, show the created transaction and a success action.
4. If status is `needs_review`, prefill the extracted fields and confidence values, let the user correct them, then `PATCH /receipts/{receipt_id}`.
5. A duplicate receipt returns a conflict response; direct the user to the existing receipt rather than uploading repeatedly.

Do not show or request an S3 object URL. Receipt originals are private and the API intentionally does not expose storage keys.

### Assistant

Send one message to `POST /chat`, optionally with the existing `conversation_id`. Store the returned conversation ID for subsequent turns. The endpoint is request/response, not streaming. Refresh affected screens when `tool_results` show that a budget, bill, receipt transaction, or category was changed.

Financial answers are assistance, not professional advice. Clearly label forecast confidence bands and warnings; do not present generated prose as a guaranteed outcome.

## 7. Loading, empty, and error states

- Use skeletons for dashboard and list reads; preserve the previous successful value during background refresh.
- Empty transactions, bills, or budgets are valid states, not errors.
- On `400`/`422`, map field validation details to the form.
- On `401`, perform the one refresh flow described above.
- On `403`, show that the action is not permitted; do not retry.
- On `404`, distinguish the resource screen from general network failure.
- On `409`, refresh the resource and explain the conflict or duplicate.
- On `429`, respect `Retry-After` if supplied and disable repeated submissions briefly.
- On `5xx`, retain local input, show a retry action, and display/copy the request ID.

Gemini can be unavailable while ordinary finance APIs continue to work. Disable only chat or receipt extraction when their service error is returned; dashboard, transactions, budgets, bills, and deterministic forecast remain usable.

## 8. Frontend acceptance checklist

- Sign-up/sign-in uses the system browser, Authorization Code, PKCE S256, and no client secret.
- Only the access token is sent to the API, and no token appears in application logs or crash reports.
- Token refresh is single-flight and every request is retried at most once after authentication failure.
- Deep links work after both authentication and logout on Android and iOS.
- Money uses integer minor units end to end and displays in the profile currency.
- All screens handle loading, empty, validation, expired session, offline, and server-error states.
- Cursor pagination preserves filters and does not duplicate list entries.
- Receipt upload validates type/size, shows progress, and supports `needs_review` correction.
- Demo seed requires destructive-action confirmation and is absent from production navigation.
- Agent writes trigger relevant provider invalidation.
- Debug UI exposes the request ID without exposing tokens, receipt contents, or sensitive account data.

