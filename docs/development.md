# Development

## Setting up

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and git. Docker is optional: it's only for running PostgreSQL locally and building the image. The commands are the same on Windows, macOS and Linux.

From the project folder:

```bash
uv sync                    # install Python 3.14 and the locked dependencies into .venv
cp .env.example .env       # in PowerShell: Copy-Item .env.example .env
uv run python manage.py migrate
uv run python manage.py createsuperuser   # a login for the admin
uv run python manage.py runserver
uv run pre-commit install  # run Ruff before each commit
```

The site is then at <http://localhost:8000>, and the admin at <http://localhost:8000/admin/>, where the projects and CV are edited and contact messages are read.

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
docs/                   This documentation, the decision records and the README's screenshots
static/
  css/
    main.css            Shared by every page: tokens, layout and components
    projects.css        The room of monitors
    case-study.css      The project write-ups
    cv.css              The CV page
    contact.css         The contact page and its confirmation
  files/                The CV and the Opus Equi dissertation as PDFs
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

Every animation has a still version, which is what the server sends. To see it, turn motion off with the button in the footer, or turn on reduced motion in your system settings. The site also switches to it by itself on devices that can't keep the animations smooth. See [ADR 4](adr/0004-animation-as-an-enhancement.md).

The intro plays once per visit, and only when the visit starts on the home page. The replay intro button in the footer plays it again.

## The investments data

The investments page is built from IBKR Activity Flex reports (see [ADR 3](adr/0003-portfolio-data-from-ibkr-flex-reports.md)). The report needs these sections: Net Asset Value (NAV) in Base, Change in NAV, Open Positions, Prior Period Positions, Trades, Cash Transactions and Financial Instrument Information, in XML.

To load a downloaded report:

```
uv run python manage.py import_flex path/to/report.xml
```

Only weights and returns are stored, never amounts of money. Days before the portfolio's inception date (set in the admin) are left out, and importing the same days again replaces them. Each import is logged under Import runs in the admin. Sleeve, sector, region and target weight are set in the admin and never changed by an import.

In production the report is downloaded each day instead (see [Deployment](deployment.md#the-daily-investments-update)). Funds held only to track a benchmark, such as the world shares fund, are marked "Benchmark only" in the admin: their closes are kept as a price series and they stay off the page.

Keep downloaded reports in a `reports/` folder, which git ignores: they hold the account's real figures.

## Quality checks

CI runs on every push to `main` and on every pull request:

1. **Lint and checks:** Ruff, formatting, missing migrations, and Django's deployment checks against the production settings.
2. **Tests:** the full suite against PostgreSQL, with coverage, which must stay above 90%.
3. **Build image:** the production Docker image, once the first two pass.

The pre-commit hooks run the same linting before each commit, so problems rarely reach CI. Dependabot opens a pull request each week for any dependency updates.
