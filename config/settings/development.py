"""Local development settings. Not for production."""

from .base import *
from .base import SECURE_CSP, env

DEBUG = True

SECRET_KEY = env.str(
    "DJANGO_SECRET_KEY",
    default="django-insecure-local-development-only-never-use-in-production",
)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "[::1]"])

# Report CSP violations rather than blocking them, so Django's debug pages
# (which use inline styles and scripts) still work.
SECURE_CSP_REPORT_ONLY = SECURE_CSP
SECURE_CSP = {}
