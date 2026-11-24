# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.14

# Build stage: install dependencies and collect static files
FROM python:${PYTHON_VERSION}-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Dependencies first, so this layer stays cached until uv.lock changes.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

COPY . .

# Placeholders: the production settings won't load without them. They only
# exist for this command and aren't kept in the image.
RUN DJANGO_SETTINGS_MODULE=config.settings.production \
    DJANGO_READ_DOT_ENV=false \
    DJANGO_SECRET_KEY=collectstatic-only \
    DJANGO_ALLOWED_HOSTS=localhost \
    DATABASE_URL=sqlite://:memory: \
    SITE_URL=http://localhost \
    /app/.venv/bin/python manage.py collectstatic --noinput

# Runtime stage: no build tools, runs as a non-root user
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    DJANGO_READ_DOT_ENV=false

# Gunicorn's control server writes to the user's home folder, so the user needs one.
RUN groupadd --system app && useradd --system --gid app --create-home --home-dir /home/app app

WORKDIR /app
COPY --from=build --chown=app:app /app /app

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz/', timeout=4)"]

# Last, as it changes on every commit and would invalidate the cached layers.
ARG GIT_SHA=""
ENV GIT_SHA=${GIT_SHA}

CMD ["gunicorn", "--config", "gunicorn.conf.py", "config.wsgi:application"]
