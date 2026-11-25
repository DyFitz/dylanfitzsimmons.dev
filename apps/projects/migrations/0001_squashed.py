"""The projects and their write-ups. Replaces the first eight migrations, which built them up
step by step; everything here can be changed in the admin."""

from django.db import migrations, models

PROJECTS = [
    {
        "title": "This site",
        "slug": "this-site",
        "summary": (
            "The source of this site: a Django application for projects, a CV, a contact "
            "form and an investment portfolio, with tests, CI and Docker from the first "
            "commit."
        ),
        "stack": "Django, PostgreSQL, Docker",
        "role": "Sole developer",
        "period": "2026 – present",
        "year": "2026",
        "status": "In progress",
        "screen": "site",
        "body": """\
## What it does

This site brings together a portfolio of software projects, an interactive CV, a contact form
and, in time, a live paper-trading portfolio. Each project has its own write-up, and the CV
links every skill to the work where it was used.

The site is also a project in its own right, built to the standard expected of production
software: tested, linted, configured from the environment, containerised, and checked
automatically on every change.

## How it works

The site is a Django 6.1 application on Python 3.14, with pages rendered on the server.
PostgreSQL stores the content in production, and SQLite is used for local development.
Projects and the CV are edited through Django's admin, so the content changes without a code
release.

On the front end, plain JavaScript modules and hand-written CSS add the animations and
interactive pieces, with no build step. Every page works without JavaScript, and every
animation has a still version, which is what the server sends first. A strict Content Security
Policy blocks inline scripts and styles throughout.

The contact form saves each message to the database and emails a notification. Spam is kept
out without a CAPTCHA, by a hidden field, a signed timing token and a rate limit on each
sender. Messages are deleted automatically after twelve months.

The site runs in a multi-stage Docker image served by Gunicorn, with static files served by
WhiteNoise. GitHub Actions runs the linting, the tests against PostgreSQL and the image build
on every push, and Dependabot keeps the dependencies up to date.

## Challenges

The main challenge was making an animated, interactive interface without leaving behind
anyone whose device or browser cannot run it. The answer was to treat animation as an
enhancement: the server always sends a complete still page, and scripts only add to it. The
site switches to the still version by itself on devices that cannot keep the animations
smooth, and when reduced motion is turned on.

The second was keeping that front end compatible with a strict security policy. With no
inline scripts or styles allowed, all behaviour lives in separate modules and all styling in
stylesheets, and the test suite checks every page for anything inline.

## Results

- 146 automated tests, with coverage held above 90% by CI.
- Every page usable with scripts turned off, and on phones, tablets and desktops.
- No inline scripts or styles anywhere, under a strict Content Security Policy.

## What's next

The next feature is an investments page: a paper-trading portfolio reported at the end of each
day from Interactive Brokers, showing returns, risk and allocation against the S&P 500 and
semiconductor benchmarks. After that come a sitemap, link previews for social media, two-step
login for the admin and error tracking.
""",
        "repo_url": "https://github.com/DyFitz/dylanfitzsimmons.dev",
        "position": 1,
        "is_published": True,
    },
    {
        "title": "Opus Equi",
        "slug": "opus-equi",
        "summary": (
            "Probabilistic forecasting of commodity spot prices: a C#/.NET 8 desktop app "
            "over a Python FastAPI service. Built as an MSc dissertation."
        ),
        "stack": (
            "C#, .NET 8, WPF, Python, FastAPI, XGBoost, scikit-learn, pandas, NumPy, "
            "statsmodels, OxyPlot"
        ),
        "role": "Sole developer, MSc dissertation",
        "period": "Jun 2025 – Aug 2025",
        "year": "2025",
        "status": "Complete",
        "screen": "forecast",
        "body": """\
## What it does

Opus Equi is a Windows desktop application for forecasting commodity spot prices. A user loads
historical price data, chooses a model and a date, and gets a chart of the observed prices and
the forecast. For future dates the forecast is a range rather than a single number: a median
estimate with a 5–95% prediction interval.

It was built as the dissertation for the MSc in Software Development at the University of
Glasgow, over nine weeks between June and August 2025. The full dissertation is available to
read: [Opus Equi dissertation (PDF)](/static/files/opus-equi-dissertation.pdf).

## How it works

The desktop client is written in C# on .NET 8, with WPF for the interface, the MVVM pattern
for the view logic and OxyPlot for the charts. It talks to a local Python service built with
FastAPI through three typed REST endpoints, one for each step of the workflow:

- **Upload:** CSV files are sent together, combined into one dataset and saved.
- **Train:** the chosen model is fitted to the dataset and saved to disk with joblib.
- **Predict:** a date within the data returns the observed price; a future date returns the
  forecast, made one day at a time, with each day's median fed into the next.

Two quantile models make the forecasts. XGBoost trains a separate model for each quantile with
a custom pinball-loss objective, which weights over- and under-prediction differently for
each, and an approximate Quantile Random Forest built on scikit-learn gives a second estimate.
Both use features such as earlier prices, rolling averages and calendar information.

The desktop app starts the service itself: it checks for Conda, creates or verifies the Python
environment, launches the server locally and waits until it answers before enabling the
workflow. If a server is already running, it uses that one instead.

The split keeps the responsibilities clear: the desktop client handles the user's choices and
the charts, and the Python service owns the data and the forecasting.

## Challenges

The forecasts depend on clean input, so the upload step had to combine several CSV files
reliably. Two problems needed separate answers: the same file uploaded twice in one batch,
and files whose date ranges overlapped.

Duplicate files are caught by a SHA-256 hash of each file's contents: a file whose hash has
already been seen in the batch is skipped. The remaining files are parsed with pandas, columns
with clashing names are renamed, and the files are joined on date, so dates from every file are
kept. The result is sorted, identical rows are dropped, and each upload is saved as a uniquely
named snapshot alongside a stable copy for the training and prediction steps. A test with files
covering different dates confirms that no price history is lost when the files don't line up.

The second was the quantile model. The XGBoost forecasts are trained on the pinball loss,
written as a custom objective. For a quantile level τ, the loss weights a forecast that falls
short by τ and one that overshoots by 1 − τ, so minimising it gives the τ-quantile of the
price rather than its mean.

The loss doesn't suit XGBoost as it stands. XGBoost sizes each step from the gradient divided
by the second derivative, the Hessian, and the pinball loss is made of straight lines, so its
second derivative is zero almost everywhere and the steps break down. The custom objective
returns the gradient, 1 − τ or −τ depending on which side of the price the forecast falls,
with a constant Hessian of 1, which keeps every step bounded and training stable.

The starting point needed the same care. XGBoost's default starting value is nowhere near a
commodity price, so the early rounds would be spent climbing towards it. Instead, each
quantile's booster starts from that quantile of the training prices. One booster is trained
for each quantile, at 5%, 50% and 95%, and the trained boosters are kept in a map keyed by
quantile.

## Results

- 15 of 18 prioritised requirements met, including all 5 must-haves, tracked in a full
  requirements traceability matrix.
- 22 automated unit tests, plus integration and acceptance suites aligned to ISO/IEC/IEEE
  29119, covering both the Python service and the C# client.
- The data pipeline validated against 27 reproducible mock datasets.
- Short user-testing sessions, whose findings became the backlog for the next version.

## What's next

- **Calibrated intervals:** a calibration step over a rolling validation window, so that real
  prices fall inside the 5–95% range as often as it promises, measured with proper scoring
  rules alongside MAE and RMSE.
- **Model versions:** each trained model is currently saved under its name and replaced by the
  next. Timestamped versions and a small model registry would allow comparison and rollback,
  and tie each forecast to the exact data and model that produced it.
- **Repeated dates:** a stated policy for dates that appear in more than one file with
  different prices, with tests for it, so the dataset holds exactly one observation per date.
- **From user testing:** clearer errors in the client, export of charts as images, and short
  help text for choosing a model.
- **The deferred features:** accuracy measures, weather analysis and derivatives pricing.
""",
        "repo_url": "https://github.com/DyFitz/CommodityPredictor",
        "position": 2,
        "is_published": True,
    },
    {
        "title": "Enular",
        "slug": "enular",
        "summary": (
            "A fintech startup making algorithmic trading easier for retail investors, and "
            "its alpha backtesting library on PyPI, built on Backtrader."
        ),
        "stack": "Python, Backtrader, Figma",
        "role": "Co-founder and software developer",
        "period": "Jun 2021 – Jan 2023",
        "year": "2021",
        "status": "Archived",
        "screen": "backtest",
        "body": """\
## What it is

Enular was a fintech startup, registered at Companies House, that set out to make algorithmic
trading tools easier for retail investors to use. Buying shares through an app had become
straightforward, but turning an idea such as "buy when two conditions are both true" into
something that could be tested consistently still took programming skills.

The proposed product was a visual strategy builder. The public release was an alpha Python
library for constructing, backtesting and evaluating strategies, built on the same idea of
reusable components. It is published on PyPI: `pip install enular`.

## How a strategy is built

A strategy is taken apart into pieces that connect together, in the way the layers of a
neural network do:

- **Indicators** turn market data into a single signal. A moving average, for example, turns
  past closing prices into a smoothed price series.
- **Indicator operations** take two signals and produce one, in three kinds: numbers to a
  number, numbers to a true-or-false signal (such as one value crossing another), and two
  true-or-false signals combined by one of seven logic gates, such as AND.
- **Strategy operations** take two signals and turn them into orders: buy or sell
  instructions, from either numbers or true-or-false signals.

New strategies can also be written by extending the library's classes and redefining their
trade logic.

The library's main example chains these together. A crossover operation compares the MACD
line with the Acceleration/Deceleration oscillator, an XOR gate combines that signal with a
second one, and an AND strategy operation turns the result into orders.

A second example trades several assets at once from a stochastic oscillator. It opens a long
position when the fast and slow lines are both below 20 and momentum is rising, and a short
position when both are above 80. Each trade is a bracket order: a limit entry 0.5% from the
close, a 3% stop-loss and a 6% take-profit, valid for ten days.

## How the library works

The library is built on Backtrader's Cerebro engine, with fixes taken from Backtrader2, the
community-maintained continuation of Backtrader. Alongside the strategy components, it
provides a collection of indicators, data streaming from Yahoo Finance and paper trading.
Cerebro is given a data feed and a
strategy, then runs the strategy over historical market data. The strategy evaluates its rules
as each new price arrives and sends orders to a simulated broker, which fills them and tracks
the positions and the portfolio's value. The result shows what the rules would have done under
the assumptions of the test.

The repository's example configures a Yahoo Finance data feed, sets a fixed position size, runs
the strategy, reports the change in portfolio value and plots the result. A second example
sweeps through different fast and slow moving-average periods and ranks the runs by Sharpe
ratio. A sweep like this shows which settings scored well on the chosen data; drawing
conclusions from it would also need testing on unseen periods and allowing for trading costs.

## The planned product

The pitch proposed a drag-and-drop web interface, with blocks for market data, indicators,
comparisons, logic and orders. A beginner could connect the blocks and test a strategy without
writing Python, while more experienced users could modify or contribute components. The design
also included tutorials and an environment for comparing backtest results.

A broker connection was planned too: investors would link their own brokerage account through
an API, starting with Interactive Brokers, so that a strategy could eventually place real
orders. Machine learning components, a strategy library, templates, documentation and a user
forum were also on the roadmap. The company's website was a
separate application, built with Django.

## What happened next

The library went through a series of pre-alpha releases on PyPI from May 2022, reaching an
alpha, version 1.0.0, in April 2023, while a visual prototype of the platform was in
development. Time and funding constraints ended development before the no-code platform and
the broker connection were built.
""",
        "repo_url": "https://github.com/enular/Enular-Library",
        "position": 3,
        "is_published": True,
    },
]


def fill_in(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    for fields in PROJECTS:
        Project.objects.get_or_create(slug=fields["slug"], defaults=fields)


class Migration(migrations.Migration):

    # The migrations this one replaces, which are on the live site already. Django
    # counts it as applied wherever all of them are.
    replaces = [
        ("projects", "0001_initial"),
        ("projects", "0002_first_projects"),
        ("projects", "0003_write_up_outlines"),
        ("projects", "0004_details_from_cv"),
        ("projects", "0005_write_ups"),
        ("projects", "0006_revisions"),
        ("projects", "0007_pinball_and_dissertation"),
        ("projects", "0008_this_site_repository"),
    ]

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=80)),
                ("slug", models.SlugField(unique=True)),
                ("summary", models.CharField(max_length=200)),
                (
                    "stack",
                    models.CharField(
                        help_text="What it's built with, separated by commas, main one first.",
                        max_length=200,
                    ),
                ),
                ("role", models.CharField(blank=True, max_length=120)),
                (
                    "period",
                    models.CharField(
                        blank=True,
                        help_text='For example "2024 – 2025".',
                        max_length=40,
                    ),
                ),
                (
                    "year",
                    models.CharField(
                        blank=True,
                        help_text="The year shown in the list.",
                        max_length=10,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        help_text='For example "In progress", "Complete", "Live" or "Archived".',
                        max_length=30,
                    ),
                ),
                (
                    "screen",
                    models.CharField(
                        choices=[
                            ("site", "A web page being drawn"),
                            ("forecast", "A forecast chart"),
                            ("backtest", "A backtest chart"),
                        ],
                        default="site",
                        max_length=20,
                    ),
                ),
                (
                    "body",
                    models.TextField(
                        blank=True, help_text="The write-up, in Markdown."
                    ),
                ),
                (
                    "repo_url",
                    models.URLField(blank=True, verbose_name="repository URL"),
                ),
                (
                    "position",
                    models.PositiveSmallIntegerField(
                        default=0, help_text="Lower numbers come first in the list."
                    ),
                ),
                ("is_published", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["position", "title"],
            },
        ),
        migrations.RunPython(fill_in, migrations.RunPython.noop),
    ]
