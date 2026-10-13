Homepage_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{APP_NAME}}</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, system-ui, sans-serif; }
    body { margin: 0; background: #0b1020; color: #e8ecf8; }
    main { max-width: 880px; margin: 0 auto; padding: 8vh 24px; }
    .badge { display: inline-block; padding: 6px 10px; border: 1px solid #445078; border-radius: 99px; }
    h1 { font-size: clamp(2.5rem, 8vw, 5.5rem); margin: 28px 0 12px; line-height: .95; }
    p { color: #aeb8d8; font-size: 1.15rem; line-height: 1.6; }
    nav { display: flex; gap: 12px; margin: 32px 0; flex-wrap: wrap; }
    a { color: white; background: #4255ff; padding: 12px 18px; border-radius: 10px; text-decoration: none; }
    a.secondary { background: #202946; }
    dl { display: grid; grid-template-columns: max-content 1fr; gap: 12px 24px; margin-top: 48px; }
    dt { color: #8290ba; } dd { margin: 0; overflow-wrap: anywhere; }
  </style>
</head>
<body><main>
  <span class="badge">{{ENV}} · v{{APP_VERSION}}</span>
  <h1>{{APP_NAME}}</h1>
  <p>{{TAGLINE}}</p>
  <nav>
    <a href="/docs">Swagger API</a>
    <a class="secondary" href="/redoc">ReDoc</a>
    <a class="secondary" href="{{API_BASE}}health/check">Health</a>
  </nav>
  <dl>
    <dt>API base</dt><dd>{{API_BASE}}</dd>
    <dt>Request ID</dt><dd>{{REQUEST_ID}}</dd>
    <dt>Architecture</dt><dd>Reusable platform services plus independently enabled product domains</dd>
  </dl>
  <p>© {{YEAR}} {{APP_NAME}}</p>
</main></body></html>"""
