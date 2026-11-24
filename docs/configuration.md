# Configuration

Settings come from environment variables. Locally, `.env` supplies them; real environment variables always take precedence.

| Variable | Needed | Purpose |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Production | Signs sessions and tokens. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `DJANGO_ALLOWED_HOSTS` | Production | Comma-separated host names the site answers to |
| `DATABASE_URL` | Production | For example `postgres://user:password@host:5432/name`. Development falls back to SQLite |
| `SITE_URL` | Production | Public base URL, used in canonical and Open Graph links |
| `DJANGO_ADMIN_URL` | Recommended | Admin path, such as `manage-7f3a/`. The deployment check warns while it's `admin/` |
| `SITE_SOURCE_URL` | Optional | Repository URL, linked from the footer |
| `GIT_SHA` | Set by the build | The commit being served, linked from the footer |
| `DJANGO_SECURE_HSTS_SECONDS` | Optional | HSTS duration, one hour by default. Raise it to `31536000` once HTTPS is confirmed working |
| `DJANGO_READ_DOT_ENV` | Optional | Set to `false` to ignore `.env` |
| `LOG_LEVEL` | Optional | `INFO` by default |
| `DJANGO_CLIENT_IP_HEADER` | Behind a proxy | The header the proxy puts the visitor's IP address in, such as `HTTP_X_FORWARDED_FOR`, for the contact form's rate limit. Without it, every visitor shares the proxy's address |
| `CONTACT_EMAIL` | Optional | Where contact form messages are emailed. `contact@dylanfitzsimmons.dev` by default |
| `DJANGO_DEFAULT_FROM_EMAIL` | Recommended | The address the site's emails come from. It needs to be one the mail server can send from |
| `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD` | Production | The mail server that sends the contact form's emails. Without them, messages are still saved and the failures logged |
| `SMTP_USE_TLS` | Optional | `true` by default, on port 587 |

In development, email is printed in the terminal instead of being sent.
