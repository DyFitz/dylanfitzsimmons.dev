import importlib

from django.db import migrations

# The details of each project, taken from my CV. A field is only changed while it still holds
# what the second migration put there, so anything already edited in the admin is kept.
FIRST = importlib.import_module("apps.projects.migrations.0002_first_projects").FIRST_PROJECTS
OUTLINES = importlib.import_module("apps.projects.migrations.0003_write_up_outlines").OUTLINE

DETAILS = {
    "this-site": {
        "role": "Sole developer",
    },
    "opus-equi": {
        "summary": (
            "Probabilistic price forecasting: a C#/.NET 8 desktop app over a Python FastAPI "
            "service. My MSc dissertation."
        ),
        "stack": "C#, .NET 8, WPF, Python, FastAPI, XGBoost, scikit-learn, pandas, OxyPlot",
        "role": "Sole developer, MSc dissertation",
        "period": "2025",
        "year": "2025",
        "status": "Complete",
    },
    "enular": {
        "summary": (
            "A fintech startup I co-founded, and its backtesting engine: an open-source Python "
            "package on PyPI, built on Backtrader."
        ),
        "stack": "Python, Backtrader, Figma",
        "role": "Co-founder and software developer",
        "period": "Jun 2021 – Jan 2023",
        "year": "2021",
        "status": "Archived",
    },
}

WRITE_UPS = {
    "opus-equi": """## What it does

Opus Equi turns raw CSV market data into probabilistic price forecasts: a median forecast with a
calibrated 5–95% prediction interval, rather than a single number. It was my dissertation for the
MSc in Software Development at the University of Glasgow.

## How it works

A C#/.NET 8 desktop client (WPF, MVVM, with charts in OxyPlot) talks to a Python FastAPI
service through three typed REST endpoints. The service runs two quantile-based models: XGBoost
trained with a custom pinball-loss objective, and an approximate Quantile Random Forest.

A deterministic data pipeline harmonises schemas, removes duplicates in time order and keeps a
timestamped snapshot of every run, so each forecast traces back to the model that made it.

## Challenges

[One or two problems that were hard to solve, and how you solved them.]

## Results

- 15 of 18 prioritised requirements met, including all 5 must-haves, tracked in a full
  requirements traceability matrix.
- 22 automated unit tests, plus integration and acceptance suites aligned to ISO/IEC/IEEE 29119.
- The pipeline validated against 27 reproducible mock datasets.

## What's next

[What you'd add or improve next, and anything you'd do differently if you started again.]
""",
    "enular": """## What it does

Enular Limited was a fintech startup I co-founded, registered at Companies House. I prototyped
its trading platform in Python, with the interface designed in Figma.

## How it works

The platform's backtesting engine is a composable framework of indicators and strategies,
built on Backtrader's Cerebro engine. It's published as an open-source package on PyPI:
`pip install enular`.

## Challenges

[One or two problems that were hard to solve, and how you solved them.]

## Results

- The backtesting engine published on PyPI.
- [Another result worth pointing out]

## What's next

[What you learned from running a startup, and what you'd do differently.]
""",
}


def fill_in(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    first = {fields["slug"]: fields for fields in FIRST}
    for project in Project.objects.filter(slug__in=DETAILS):
        changed = []
        for field, value in DETAILS[project.slug].items():
            if getattr(project, field) == first[project.slug][field]:
                setattr(project, field, value)
                changed.append(field)
        if project.slug in WRITE_UPS and project.body == OUTLINES.format(title=project.title):
            project.body = WRITE_UPS[project.slug]
            changed.append("body")
        if changed:
            project.save(update_fields=changed)


class Migration(migrations.Migration):
    dependencies = [("projects", "0003_write_up_outlines")]

    # Going back leaves the details as they are: nothing here is needed for the site to work.
    operations = [migrations.RunPython(fill_in, migrations.RunPython.noop)]
