"""Settings shared by every environment.

Secrets and anything that varies between environments come from environment
variables (see .env.example). development.py, test.py and production.py only
override what differs.
"""

from pathlib import Path

import environ
from django.utils.csp import CSP

BASE_DIR = Path(__file__).resolve().parents[2]

env = environ.Env()

# Real environment variables take precedence over .env. The Docker image sets
# DJANGO_READ_DOT_ENV=false so it never reads one.
if env.bool("DJANGO_READ_DOT_ENV", default=True) and (BASE_DIR / ".env").is_file():
    env.read_env(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

DEBUG = False  # Only switched on in development.py.

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # Serves static files through WhiteNoise under runserver too, as in production.
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    # Local apps
    "apps.core",
    "apps.projects",
    "apps.cv",
    "apps.contact",
]

MIDDLEWARE = [
    # Must stay first: see HealthCheckMiddleware.
    "apps.core.middleware.HealthCheckMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site",
            ],
        },
    },
]

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

# SQLite locally so there's nothing to set up. CI and production use PostgreSQL.
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static and media files
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Compressed, with hashed filenames so browsers can cache them indefinitely.
    "staticfiles": {"BACKEND": "apps.core.storage.StaticStorage"},
}

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

# Console by default, so nothing gets sent by accident. production.py switches
# to SMTP (Django's deploy checks fail if it doesn't), and the test runner swaps
# in the locmem backend.
MAILERS = {
    "default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"},
}

# Where messages from the contact form go, and who they come from. The sender's address is
# put in Reply-To, never From, as mail servers reject mail claiming to be from addresses
# they don't handle.
CONTACT_EMAIL = env.str("CONTACT_EMAIL", default="contact@dylanfitzsimmons.dev")
DEFAULT_FROM_EMAIL = env.str("DJANGO_DEFAULT_FROM_EMAIL", default="webmaster@localhost")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

ADMIN_URL = env.str("DJANGO_ADMIN_URL", default="admin/")

# The request header the hosting platform's proxy puts the visitor's IP address in, e.g.
# HTTP_X_FORWARDED_FOR. Empty means REMOTE_ADDR, which is right with no proxy in front. Only
# set it behind a proxy that always sets the header, or anyone could fake their address.
CLIENT_IP_HEADER = env.str("DJANGO_CLIENT_IP_HEADER", default="")

# Only this site's own files can load, inline scripts and styles are blocked,
# and no other site can frame the pages.
SECURE_CSP = {
    "default-src": [CSP.SELF],
    "base-uri": [CSP.SELF],
    "connect-src": [CSP.SELF],
    "font-src": [CSP.SELF],
    "form-action": [CSP.SELF],
    "frame-ancestors": [CSP.NONE],
    "img-src": [CSP.SELF],
    "object-src": [CSP.NONE],
    "script-src": [CSP.SELF],
    "style-src": [CSP.SELF],
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

# Everything goes to stdout for the hosting platform to collect.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
    },
    "root": {"handlers": ["console"], "level": env.str("LOG_LEVEL", default="INFO")},
    "loggers": {
        # Stops Django's default handler logging everything a second time.
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# ---------------------------------------------------------------------------
# Site identity (available in templates as `site`)
# ---------------------------------------------------------------------------

SITE_NAME = "Dylan Fitzsimmons"
SITE_TAGLINE = "Software developer"
SITE_DESCRIPTION = (
    "The coding projects, CV and investment portfolio of Dylan Fitzsimmons, a software developer."
)
SITE_URL = env.str("SITE_URL", default="http://localhost:8000").rstrip("/")
SITE_SOURCE_URL = env.str("SITE_SOURCE_URL", default="").rstrip("/")
# Commit being served, set when the Docker image is built.
GIT_SHA = env.str("GIT_SHA", default="")
