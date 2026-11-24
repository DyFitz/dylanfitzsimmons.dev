from .base import *
from .base import STORAGES, env

SECRET_KEY = "insecure-test-only-key"  # noqa: S105
ALLOWED_HOSTS = ["testserver", "localhost"]

# In-memory SQLite unless DATABASE_URL is set (CI uses PostgreSQL).
DATABASES = {"default": env.db("DATABASE_URL", default="sqlite://:memory:")}

# Much faster than the default hasher. Fine for tests only.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# No email setting needed: the test runner switches MAILERS to the locmem
# backend, which collects sent messages in django.core.mail.outbox.

# The manifest storage only works after collectstatic has run.
STORAGES = {
    **STORAGES,
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
# Stops WhiteNoise warning that STATIC_ROOT doesn't exist.
WHITENOISE_AUTOREFRESH = True
