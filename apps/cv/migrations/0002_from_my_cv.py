import datetime

from django.db import migrations

# My CV as of November 2026. Everything here can be changed in the admin; text in square
# brackets is still to be written.
PROFILE = {
    "name": "Dylan Fitzsimmons",
    "role": "Software developer · Glasgow",
    "looking_for": "Looking for a graduate software engineering role in financial technology.",
    "summary": (
        "MSc Software Development graduate with a background in engineering and financial "
        "economics. I built Opus Equi, a desktop forecasting application with a C#/.NET 8 client "
        "over a Python FastAPI service, and took it from requirements through to unit, "
        "integration and acceptance testing. As co-founder of Enular, a fintech startup, I "
        "designed the platform's backtesting engine and published it as a Python package on PyPI."
    ),
    "github_url": "https://github.com/DyFitz",
    "linkedin_url": "https://www.linkedin.com/in/dylan-fitzsimmons",
    "updated": datetime.date(2026, 11, 15),
}

READOUTS = [
    ("MSc × 2 · BEng", "Software development, financial economics and engineering"),
    ("Python · C# · Java", "The languages I've built the most with"),
    ("IESIS award", "Best Student: the top Honours result in my year"),
]

ENTRIES = [
    {
        "kind": "education",
        "title": "MSc Software Development",
        "organisation": "University of Glasgow",
        "started": "Sep 2024",
        "ended": "Dec 2025",
        "summary": (
            "Java backend development, Agile methods and software engineering practice. "
            "Dissertation: Opus Equi."
        ),
        "more": (
            "[Courses, team projects and anything else worth knowing: the turn-based strategy "
            "game and SRC Events were both team projects here.]"
        ),
        "project": "opus-equi",
    },
    {
        "kind": "education",
        "title": "MSc Financial Economics",
        "organisation": "University of Glasgow",
        "started": "Sep 2018",
        "ended": "Dec 2019",
        "summary": (
            "Asset pricing, mathematical finance and computational finance. Coursework in C++ "
            "(stochastic calculus for options) and MATLAB (nonlinear volatility models)."
        ),
        "more": "[Your dissertation, if there was one, and what the course gave you that you use now.]",
    },
    {
        "kind": "education",
        "title": "BEng (Hons) Mechanical and Power Plant Systems Engineering",
        "organisation": "Glasgow Caledonian University",
        "started": "Sep 2014",
        "ended": "Jul 2018",
        "summary": (
            "Mechatronics, energy systems and computational methods; MATLAB for PID controller "
            "design and thermodynamic simulations."
        ),
        "award": "IESIS Best Student Award · top Honours result in cohort",
    },
    {
        "kind": "experience",
        "title": "A&E Call Handler",
        "organisation": "NHS 24, Glasgow",
        "started": "Jan 2023",
        "ended": "",
        "summary": (
            "Independent, protocol-driven casework in a 24/7 emergency service, kept up alongside "
            "full-time postgraduate study."
        ),
        "more": (
            "[What the job asks of you, and what it taught you that carries over to software: "
            "working calmly under pressure, following a protocol exactly, explaining things "
            "clearly.]"
        ),
    },
    {
        "kind": "experience",
        "title": "Co-Founder and Software Developer",
        "organisation": "Enular Limited",
        "started": "Jun 2021",
        "ended": "Jan 2023",
        "points": (
            "Co-founded a fintech startup registered at Companies House, and prototyped its "
            "trading platform in Python, with the interface designed in Figma.\n"
            "Designed the backtesting engine and published it as an open-source package on PyPI: "
            "a composable framework of indicators and strategies built on Backtrader's Cerebro "
            "engine."
        ),
        "more": (
            "[What running a startup involved beyond the code: who did what, what the platform "
            "was for, and why it ended.]"
        ),
        "project": "enular",
    },
]

PROJECTS = [
    {
        "title": "Opus Equi: financial time-series forecasting",
        "meta": "MSc dissertation · 2025",
        "stack": (
            "C# / .NET 8 (WPF, MVVM), Python / FastAPI, XGBoost, scikit-learn, pandas, OxyPlot, "
            "pytest, MSTest"
        ),
        "points": (
            "A full-stack desktop application: a C#/.NET 8 WPF client over a Python FastAPI "
            "service, with three typed REST endpoints that turn raw CSV market data into "
            "probabilistic price forecasts.\n"
            "Two quantile-based models (XGBoost with a custom pinball-loss objective, and an "
            "approximate Quantile Random Forest) giving median forecasts with calibrated 5–95% "
            "prediction intervals."
        ),
        "more_points": (
            "A deterministic data pipeline (schema harmonisation, chronological deduplication, "
            "timestamped snapshots) validated against 27 reproducible mock datasets, so every "
            "forecast traces back to a saved model.\n"
            "22 automated unit tests plus integration and acceptance suites aligned to "
            "ISO/IEC/IEEE 29119; 15 of 18 prioritised requirements met, including all 5 "
            "must-haves, against a full traceability matrix."
        ),
        "write_up": "opus-equi",
        "is_key": True,
    },
    {
        "title": "SRC Events Management",
        "meta": "team of 3",
        "stack": "Django, SQLite, Render",
        "summary": (
            "An events platform for university societies. I owned the backend: framework set-up, "
            "security, authentication, the database layer and deployment on Render, with email "
            "through ProtonMail Bridge."
        ),
    },
    {
        "title": "Turn-based strategy game",
        "meta": "team project",
        "stack": "Java, Play Framework, WebSockets",
        "summary": (
            "I designed the core architecture (game and turn managers, and the class hierarchy "
            "for units and cards) and wrote the enemy AI, with real-time updates over WebSockets."
        ),
    },
]

# Where each skill was used. A slug links to that project's write-up.
SKILLS = {
    "Languages": [
        ("Python", [("Opus Equi", "opus-equi"), ("Enular", "enular"), ("This site", "this-site"), "SRC Events"]),
        ("C#", [("Opus Equi", "opus-equi")]),
        ("Java", ["MSc Software Development", "Strategy game"]),
        ("C++", ["MSc Financial Economics: options pricing"]),
        ("JavaScript", [("This site", "this-site"), "[where else]"]),
        ("MATLAB", ["BEng: PID control, thermodynamics", "MSc Financial Economics: volatility models"]),
        ("SQL", [("PostgreSQL · this site", "this-site"), "SQLite · SRC Events", "[MySQL: where]"]),
    ],
    "Frameworks and libraries": [
        (".NET 8 / WPF", [("Opus Equi", "opus-equi")]),
        ("FastAPI", [("Opus Equi", "opus-equi")]),
        ("Django", [("This site", "this-site"), "SRC Events"]),
        ("XGBoost, scikit-learn, pandas", [("Opus Equi", "opus-equi")]),
        ("NumPy, SciPy, statsmodels", ["[where used]"]),
        ("Backtrader", [("Enular", "enular")]),
        ("React", ["[where used]"]),
    ],
    "Tools": [
        ("Git", ["Every project"]),
        ("Render", ["SRC Events"]),
        ("Figma", [("Enular", "enular")]),
        ("Bloomberg Terminal, EViews", ["[where used]"]),
        ("PowerShell", ["[where used]"]),
    ],
}


def add_cv(apps, schema_editor):
    Profile = apps.get_model("cv", "Profile")
    Readout = apps.get_model("cv", "Readout")
    Entry = apps.get_model("cv", "Entry")
    CvProject = apps.get_model("cv", "CvProject")
    SkillGroup = apps.get_model("cv", "SkillGroup")
    Skill = apps.get_model("cv", "Skill")
    Evidence = apps.get_model("cv", "Evidence")
    write_ups = {project.slug: project for project in apps.get_model("projects", "Project").objects.all()}

    Profile.objects.create(**PROFILE)
    for position, (value, label) in enumerate(READOUTS):
        Readout.objects.create(value=value, label=label, position=position)
    for position, entry in enumerate(ENTRIES):
        fields = dict(entry)
        slug = fields.pop("project", None)
        Entry.objects.create(**fields, project=write_ups.get(slug), position=position)
    for position, project in enumerate(PROJECTS):
        fields = dict(project)
        slug = fields.pop("write_up", None)
        CvProject.objects.create(**fields, write_up=write_ups.get(slug), position=position)
    for group_position, (title, skills) in enumerate(SKILLS.items()):
        group = SkillGroup.objects.create(title=title, position=group_position)
        for skill_position, (name, evidence) in enumerate(skills):
            skill = Skill.objects.create(group=group, name=name, position=skill_position)
            for item_position, item in enumerate(evidence):
                label, slug = item if isinstance(item, tuple) else (item, None)
                Evidence.objects.create(
                    skill=skill, label=label, project=write_ups.get(slug), position=item_position
                )


def remove_cv(apps, schema_editor):
    for name in ("Evidence", "Skill", "SkillGroup", "CvProject", "Entry", "Readout", "Profile"):
        apps.get_model("cv", name).objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("cv", "0001_initial")]

    operations = [migrations.RunPython(add_cv, remove_cv)]
