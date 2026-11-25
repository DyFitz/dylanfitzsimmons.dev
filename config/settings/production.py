"""Production settings.

Required values have no defaults, so the site won't start without them.
"""

from config.sentry import start as start_error_tracking

from .base import *
from .base import GIT_SHA, env

DEBUG = False

SECRET_KEY = env.str("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
SITE_URL = env.str("SITE_URL").rstrip("/")

DATABASES = {
    "default": {
        **env.db("DATABASE_URL"),
        "CONN_MAX_AGE": env.int("DJANGO_CONN_MAX_AGE", default=60),
        "CONN_HEALTH_CHECKS": True,
    },
}

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

# Optional, so the image builds and the checks run without a mail server. Until it's set,
# contact messages are still saved, and the failed emails are logged. The port is left to
# Django: 587 with TLS.
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": env.str("SMTP_HOST", default="localhost"),
            "username": env.str("SMTP_USERNAME", default=""),
            "password": env.str("SMTP_PASSWORD", default=""),
            "use_tls": env.bool("SMTP_USE_TLS", default=True),
            "timeout": 10,
        },
    },
}
DEFAULT_FROM_EMAIL = env.str("DJANGO_DEFAULT_FROM_EMAIL", default="website@dylanfitzsimmons.dev")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ---------------------------------------------------------------------------
# HTTPS
# ---------------------------------------------------------------------------

# TLS ends at the hosting platform's proxy, which passes the original scheme in
# this header. Only safe behind a proxy that always sets it.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Browsers cache HSTS for the whole period, so start short and raise it to a
# year (31536000) once HTTPS is confirmed working.
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=False)

if not SECURE_HSTS_PRELOAD:
    # Preloading is hard to undo, so silence the check that recommends it until
    # it's switched on.
    SILENCED_SYSTEM_CHECKS = ["security.W021"]

# ---------------------------------------------------------------------------
# Error tracking
# ---------------------------------------------------------------------------

# Optional: until it's set, errors are only logged. See config/sentry.py for what's sent.
SENTRY_DSN = env.str("SENTRY_DSN", default="")
start_error_tracking(SENTRY_DSN, release=GIT_SHA)
