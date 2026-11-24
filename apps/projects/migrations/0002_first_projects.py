from django.db import migrations

# The three projects the site starts with. Text in square brackets is still to be filled in,
# which can be done in the admin.
FIRST_PROJECTS = [
    {
        "slug": "this-site",
        "title": "This site",
        "summary": (
            "A Django site for my projects, CV and investments, built with tests, CI and Docker "
            "from the first commit."
        ),
        "stack": "Django, PostgreSQL, Docker",
        "role": "[Your role]",
        "period": "2026 – present",
        "year": "2026",
        "status": "In progress",
        "screen": "site",
        "position": 1,
    },
    {
        "slug": "opus-equi",
        "title": "Opus Equi",
        "summary": "Financial time-series forecasting, with a Python API and a C# desktop app.",
        "stack": "Python, FastAPI, C#, WPF",
        "role": "[Your role]",
        "period": "[Start] – [end]",
        "year": "[Year]",
        "status": "[Status]",
        "screen": "forecast",
        "position": 2,
    },
    {
        "slug": "enular",
        "title": "Enular",
        "summary": "A backtesting engine for trading strategies, built in Python on Backtrader.",
        "stack": "Python, Backtrader",
        "role": "[Your role]",
        "period": "[Start] – [end]",
        "year": "[Year]",
        "status": "[Status]",
        "screen": "backtest",
        "position": 3,
    },
]


def add_first_projects(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    for fields in FIRST_PROJECTS:
        Project.objects.get_or_create(slug=fields["slug"], defaults=fields)


def remove_first_projects(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    Project.objects.filter(slug__in=[fields["slug"] for fields in FIRST_PROJECTS]).delete()


class Migration(migrations.Migration):
    dependencies = [("projects", "0001_initial")]

    operations = [migrations.RunPython(add_first_projects, remove_first_projects)]
