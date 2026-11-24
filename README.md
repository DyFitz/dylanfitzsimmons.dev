# dylanfitzsimmons.dev

The source code for [dylanfitzsimmons.dev](https://dylanfitzsimmons.dev): my coding projects, CV, investment portfolio and a contact form, built with Django.

The site is a project in its own right, so it's built the way production software should be: tested, linted, configured from the environment, containerised, and checked by CI on every push.

## Status

| Phase | What it adds | State |
| --- | --- | --- |
| 1. Foundation | Settings, health check, tests, CI, Docker | Done |
| 2. Layout and home page | Header, footer and the home page, with its intro and animations and a still version of everything | Done |
| 3. Projects | Projects edited in the admin, shown on three monitors in a room, with a write-up for each | Done |
| 4. CV | CV page from the database, and a one-page PDF | Done |
| 5. Contact | Messages saved to the database, email notifications, spam protection | Done |
| 6. Mobile layout | Every page laid out for phones and tablets | Next |
| 7. Deployment | Hosting, the domain, email and HTTPS | Planned |
| 8. Investments | Daily IBKR Flex snapshots, allocation and performance charts | Planned |
| 9. Polish | Sitemap, Open Graph images, admin two-factor login, error tracking, type checking | Planned |

## Stack

- **Python 3.14** and **Django 6.1**, with server-rendered templates
- **Plain JavaScript modules** and plain CSS (a shared stylesheet, plus one for each page that needs more), with no build step
- **PostgreSQL** in CI and production; SQLite for zero-setup local development
- **uv** for dependencies, with a lockfile for reproducible installs
- **pytest** with pytest-django; coverage must stay above 90%
- **Ruff** for linting and formatting, run by pre-commit hooks and CI
- **Docker** multi-stage image, served by **Gunicorn**, with static files served by **WhiteNoise**
- **GitHub Actions** for CI and **Dependabot** for weekly dependency updates

## Getting started

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and git. Docker is optional: it's only for running PostgreSQL locally and building the image. The commands are the same on Windows, macOS and Linux.

From the project folder:

```bash
uv sync                    # install Python 3.14 and the locked dependencies into .venv
cp .env.example .env       # in PowerShell: Copy-Item .env.example .env
uv run python manage.py migrate
uv run python manage.py createsuperuser   # a login for the admin
uv run python manage.py runserver
```

The site is then at <http://localhost:8000>, and the admin at <http://localhost:8000/admin/>, where the projects and CV are edited and contact messages are read. Once the folder is a git repository, `uv run pre-commit install` adds the git hooks.

`uv.lock` records the exact version of every dependency. uv updates it whenever `pyproject.toml` changes; commit it along with the change.

## Everyday commands

| Command | What it does |
| --- | --- |
| `uv run python manage.py runserver` | Start the development server |
| `uv run pytest --cov` | Run the tests with coverage |
| `uv run ruff check .` | Check for lint problems |
| `uv run ruff check --fix .` | Fix the lint problems Ruff can fix by itself |
| `uv run ruff format .` | Format the code |
| `uv run python manage.py makemigrations --check --dry-run` | Check that every model change has a migration |
| `uv run python manage.py migrate` | Bring the database up to date with the migrations |
| `uv run python manage.py createsuperuser` | Make a login for the admin |
| `uv run python manage.py delete_old_messages` | Delete contact messages older than 12 months |
| `docker compose up -d db` | Start PostgreSQL in Docker |
| `docker build -t dylanfitzsimmons-dev .` | Build the production image |

## Project structure

```text
apps/                   One Django app per feature, each with its own templates and tests
  core/                 Layout, home page, navigation, health check, system checks
  projects/             Projects, the room of monitors and the write-ups
  cv/                   The CV page, from the database
  contact/              The contact form, its spam checks and the confirmation page
config/
  settings/
    base.py             Shared settings: how the site works
    development.py      Local overrides: debug on, email printed to the console
    test.py             Fast, isolated settings for the test suite
    production.py       Everything from the environment; refuses to start if incomplete
  urls.py
  wsgi.py
docs/adr/               Architecture decision records
static/
  css/
    main.css            Shared by every page: tokens, layout and components
    projects.css        The room of monitors
    case-study.css      The project write-ups
    cv.css              The CV page
    contact.css         The contact page and its confirmation
  files/                The CV as a PDF
  fonts/                TeX Gyre Heros, VT323 and Michroma, with their licences
  img/                  Icons, textures and still images of the animations
  js/
    head.js             Runs before first paint: theme, motion and intro settings
    site.js             Every page: header readout, motion and theme buttons
    home.js             The home page's intro, console and animations
    projects.js         The room of monitors
    project.js          A project's write-up
    contact.js          The contact page's globe and character count
    modules/            One module per feature, shared between pages
templates/              Base layout, shared includes and error pages
```

Each new feature is a new app under `apps/`, with its own models, views, templates, URLs and tests.

## Front end

Pages are rendered on the server and work without JavaScript; scripts only add to them. The Content Security Policy blocks inline scripts and styles, so there are none, and the tests check for them.

Colours and fonts are defined once, in the tokens layer of `main.css` (with a few more in the page stylesheets that need them), and the canvases read the same values, so a colour change only happens in one place.

Every animation has a still version, which is what the server sends. To see it, turn motion off with the button in the footer, or turn on reduced motion in your system settings. The site also switches to it by itself on devices that can't keep the animations smooth. See [ADR 4](docs/adr/0004-animation-as-an-enhancement.md).

The intro plays once per visit, in each browser tab. The replay intro button in the footer plays it again.

## Configuration

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

## Quality checks

CI runs on every push to `main` and on every pull request:

1. **Lint and checks:** Ruff, formatting, missing migrations, and Django's deployment checks against the production settings.
2. **Tests:** the full suite against PostgreSQL, with coverage.
3. **Build image:** the production Docker image, once the first two pass.

The pre-commit hooks run the same linting before each commit, so problems rarely reach CI.

## Deployment

The `Dockerfile` builds a small image that runs as an unprivileged user, with static files already collected. On any platform that runs containers:

1. Set the production environment variables above.
2. Run `python manage.py migrate` as a release or pre-deploy step rather than on container start, so two instances never migrate at once.
3. Point the platform's health check at `/healthz/`. It answers before host validation and HTTPS redirects, and returns 503 if the database is unreachable.
4. Schedule `python manage.py delete_old_messages` to run daily. It deletes contact messages older than 12 months, as the contact page's privacy note promises. (Old messages are also cleared out whenever a new one arrives, as a fallback.)

In production, HTTP redirects to HTTPS, cookies are sent over HTTPS only, and pages carry a strict Content Security Policy.

## Design decisions

Significant decisions are recorded as architecture decision records in [`docs/adr`](docs/adr):

1. [Server-rendered pages, not a single-page app](docs/adr/0001-server-rendered-pages.md)
2. [Configuration from the environment](docs/adr/0002-configuration-from-the-environment.md)
3. [Portfolio data from IBKR Flex reports](docs/adr/0003-portfolio-data-from-ibkr-flex-reports.md)
4. [Animation as an enhancement, with a still version of every page](docs/adr/0004-animation-as-an-enhancement.md)
