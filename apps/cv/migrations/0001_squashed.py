"""The CV, from the CV of November 2026. Replaces the first eight migrations, which built it up
step by step; everything here can be changed in the admin."""

from datetime import date

import django.db.models.deletion
from django.db import migrations, models

PROFILE = {
    "name": "Dylan Fitzsimmons",
    "role": "Software developer · Glasgow",
    "looking_for": "Looking for a graduate software engineering role in financial technology.",
    "summary": (
        "MSc Software Development graduate with a background in engineering and financial "
        "economics. Built Opus Equi, a desktop forecasting application with a C#/.NET 8 "
        "client over a Python FastAPI service, and took it from requirements through to "
        "unit, integration and acceptance testing. As co-founder of Enular, a fintech "
        "startup, designed the platform's backtesting engine and published it as a Python "
        "package on PyPI."
    ),
    "github_url": "https://github.com/DyFitz",
    "linkedin_url": "https://www.linkedin.com/in/dylan-fitzsimmons",
    "updated": "2026-11-15",
}
READOUTS = [
    ("MSc × 2 · BEng", "Software development, financial economics and engineering"),
    ("Python · C# · Java", "The languages used most"),
    ("IESIS award", "Best Student: the top Honours result in the year"),
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
        "more": """\
- Dissertation: Opus Equi, built from June to August 2025 ([read it as a PDF](/static/files/opus-equi-dissertation.pdf)).

**Team projects**

- SRC Events, a team of three: an events platform for university societies. Responsible for the Django backend and its integration with the front end.
- Turn-based strategy game in Java, a team of four: Scrum Master; designed the core architecture and wrote the enemy AI.
- Software engineering, a team of six: Product Owner for a system to manage part-time teachers, written in Java. Prioritised the backlog, wrote user stories and planned three two-week iterations.
- Enterprise cyber security, a team of five: a risk assessment of messaging apps (WhatsApp, Telegram and Signal) in a financial firm, using the ENISA framework against GDPR, DORA and MiFID II.

**Coursework**

- Advanced programming: a concurrent task runner in Java, with threads, cancellation and tasks that wait on others; the Composite pattern for a file system.
- Algorithms and data structures: linked-list algorithms and set operations in Java.
- Databases: normalisation to fourth normal form, and SQL including window functions.
- Cyber security: an analysis of the 2024 Dell data breach, from the API weaknesses exploited to the company's response.
- Systems and networks: assembly language for the Sigma16 architecture.
- Programming: Connect Four in Java.""",
        "project": "opus-equi",
    },
    {
        "kind": "education",
        "title": "MSc Financial Economics",
        "organisation": "University of Glasgow",
        "started": "Sep 2018",
        "ended": "Dec 2019",
        "summary": (
            "Asset pricing, mathematical finance and computational finance. Coursework in "
            "C++ (stochastic calculus for options) and MATLAB (nonlinear volatility "
            "models)."
        ),
        "more": """\
- Dissertation: Brexit and the efficiency of the foreign exchange market, for sterling against the euro and the US dollar.
- Bloomberg Terminal and EViews for market data and econometrics.
- 2nd place, GUTIC Stock Pitch (Glasgow University Trading and Investment Club, Feb 2019), in a team of two: a pitch on BMW Group to judges from firms including KPMG and Smith & Williamson.
- 2nd place and the prize for best presentation slides, ASES & GUCS Business Case Competition (Jan 2019): presented at the Grosvenor Hilton, Glasgow, to nine judges and around 120 guests.""",
        "position": 1,
    },
    {
        "kind": "education",
        "title": "BEng (Hons) Mechanical and Power Plant Systems Engineering",
        "organisation": "Glasgow Caledonian University",
        "started": "Sep 2014",
        "ended": "Jul 2018",
        "summary": (
            "Mechatronics, energy systems and computational methods; MATLAB for PID "
            "controller design and thermodynamic simulations."
        ),
        "award": "IESIS Best Student Award · top Honours result in cohort",
        "position": 2,
    },
    {
        "kind": "education",
        "title": "European Project Semester (Erasmus exchange)",
        "organisation": "University POLITEHNICA of Bucharest",
        "started": "Feb 2017",
        "ended": "Jun 2017",
        "summary": (
            "Cross-discipline engineering project in a team of six students from across "
            "Europe: the research, design and construction of a 3D-printed prosthetic hand,"
            " using MATLAB."
        ),
        "award": "Grade: 100%",
        "position": 5,
    },
    {
        "kind": "experience",
        "title": "A&E Call Handler",
        "organisation": "NHS 24, Glasgow",
        "started": "Jan 2023",
        "summary": (
            "Independent, protocol-driven casework in a 24/7 emergency service, kept up "
            "alongside full-time postgraduate study."
        ),
        "more": (
            "The first point of contact for people calling 111, NHS 24's urgent care "
            "service for Scotland. Each call means capturing the caller's details and "
            "symptoms accurately and following the triage process, so that the call is "
            "passed to the right clinician, such as a nurse, pharmacist or dental nurse, or"
            " straight to the Scottish Ambulance Service when a life is at risk. The calls "
            "cover a wide range of conditions and need a calm, confident and empathetic "
            "manner throughout. The role has continued alongside full-time postgraduate "
            "study, and it carries over to software: staying calm under pressure, following"
            " a process exactly, and handing work on with clear records."
        ),
        "position": 3,
    },
    {
        "kind": "experience",
        "title": "Co-Founder and Software Developer",
        "organisation": "Enular Limited",
        "started": "Jun 2021",
        "ended": "Jan 2023",
        "points": """\
Co-founded a fintech startup registered at Companies House, and prototyped its trading platform in Python, with the interface designed in Figma.
Designed the backtesting engine and published it as an open-source package on PyPI: a composable framework of indicators and strategies built on Backtrader's Cerebro engine.""",
        "more": """\
- A fintech startup making algorithmic trading tools easier for retail investors to use.
- Proposed product: a drag-and-drop strategy builder, with blocks for market data, indicators, comparisons, logic and orders, plus tutorials and a broker connection.
- Released an alpha Python library on PyPI for building, backtesting and evaluating strategies from reusable components.
- Development ended before the visual platform was built, owing to time and funding.""",
        "project": "enular",
        "position": 4,
    },
    {
        "kind": "experience",
        "title": "English Teacher",
        "organisation": "EF English First, Shanghai",
        "started": "Oct 2019",
        "ended": "Oct 2020",
        "summary": "Full-time English teacher.",
        "points": """\
Planned lessons around grammar, writing structure and the language students need for study and work.
Assessed ability through standardised testing, tracked each student's progress and reported back to parents.""",
        "position": 6,
    },
    {
        "kind": "experience",
        "title": "Mechanical Engineering Intern",
        "organisation": "Changzhou Xingyu Automotive Lighting Systems, China",
        "started": "Jul 2017",
        "ended": "Sep 2017",
        "summary": (
            "Material Science and Research department of a tier 1 automotive lighting "
            "supplier, whose clients include Toyota, BMW and Volkswagen."
        ),
        "points": """\
Batch-tested supplier materials, including SABIC plastics, with tensile, shear, compression, fatigue and hardness tests, and thermal ageing to simulate long-term wear.
Inspected LEDs for imperfections with a scanning electron microscope, and tested plastic coatings on headlight lenses.
Presented findings to the research team weekly, and carried out quality checks with the factory attached to the research centre.
Supported the research for the team leader's PhD thesis.""",
        "position": 7,
    },
]
CV_PROJECTS = [
    {
        "title": "Opus Equi: financial time-series forecasting",
        "meta": "MSc dissertation · 2025",
        "stack": (
            "C# / .NET 8 (WPF, MVVM), Python / FastAPI, XGBoost, scikit-learn, pandas, "
            "OxyPlot, pytest, MSTest"
        ),
        "points": """\
A full-stack desktop application: a C#/.NET 8 WPF client over a Python FastAPI service, with three typed REST endpoints that turn raw CSV market data into probabilistic price forecasts.
Two quantile-based models (XGBoost with a custom pinball-loss objective, and an approximate Quantile Random Forest) giving median forecasts with 5–95% prediction intervals.""",
        "more_points": """\
A deterministic data pipeline (schema harmonisation, chronological deduplication, timestamped snapshots) validated against 27 reproducible mock datasets, so every forecast traces back to a saved model.
22 automated unit tests plus integration and acceptance suites aligned to ISO/IEC/IEEE 29119; 15 of 18 prioritised requirements met, including all 5 must-haves, against a full traceability matrix.""",
        "write_up": "opus-equi",
        "is_key": True,
    },
    {
        "title": "SRC Events Management",
        "meta": "team of 3",
        "stack": "Django, SQLite, Render",
        "summary": (
            "An events platform for university societies. Responsible for the backend: "
            "framework set-up, security, authentication, the database layer and deployment "
            "on Render, with email through ProtonMail Bridge."
        ),
        "position": 1,
    },
    {
        "title": "Turn-based strategy game",
        "meta": "team of 4",
        "stack": "Java, Play Framework, WebSockets",
        "summary": (
            "Designed the core architecture (game and turn managers, and the class "
            "hierarchy for units and cards) and wrote the enemy AI, with real-time updates "
            "over WebSockets."
        ),
        "position": 2,
    },
]
# Each group's skills, and where each was used: (label, project write-up's slug).
SKILLS = [
    ("Languages", [
        ("Python", [("Opus Equi", "opus-equi"), ("Enular", "enular"), ("This site", "this-site"), ("SRC Events", None)]),
        ("C#", [("Opus Equi", "opus-equi")]),
        ("Java", [("MSc Software Development", None), ("Strategy game", None)]),
        ("C++", [("MSc Financial Economics: options pricing", None)]),
        ("JavaScript", [("This site", "this-site"), ("SRC Events", None)]),
        ("MATLAB", [("BEng: PID control, thermodynamics", None), ("MSc Financial Economics: volatility models", None)]),
        ("SQL", [("PostgreSQL · this site", "this-site"), ("SQLite · SRC Events", None), ("MySQL · university coursework", None)]),
    ]),
    ("Frameworks and libraries", [
        (".NET 8 / WPF", [("Opus Equi", "opus-equi")]),
        ("FastAPI", [("Opus Equi", "opus-equi")]),
        ("Django", [("This site", "this-site"), ("SRC Events", None)]),
        ("XGBoost, scikit-learn, pandas", [("Opus Equi", "opus-equi")]),
        ("NumPy, SciPy, statsmodels", [("NumPy, SciPy, statsmodels · Opus Equi", "opus-equi"), ("statsmodels · Enular", "enular")]),
        ("Backtrader", [("Enular", "enular")]),
    ]),
    ("Tools", [
        ("Git", [("Every project", None)]),
        ("Render", [("SRC Events", None)]),
        ("Figma", [("Enular", "enular")]),
        ("Bloomberg Terminal, EViews", [("MSc Financial Economics", None)]),
        ("PowerShell", [("University projects", None)]),
    ]),
]


def fill_in(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    Profile = apps.get_model("cv", "Profile")
    Readout = apps.get_model("cv", "Readout")
    Entry = apps.get_model("cv", "Entry")
    CvProject = apps.get_model("cv", "CvProject")
    SkillGroup = apps.get_model("cv", "SkillGroup")
    Skill = apps.get_model("cv", "Skill")
    Evidence = apps.get_model("cv", "Evidence")
    if Profile.objects.exists():
        return
    projects = {project.slug: project for project in Project.objects.all()}

    Profile.objects.create(**{**PROFILE, "updated": date.fromisoformat(PROFILE["updated"])})
    for position, (value, label) in enumerate(READOUTS):
        Readout.objects.create(value=value, label=label, position=position)
    for fields in ENTRIES:
        Entry.objects.create(**{**fields, "project": projects.get(fields.get("project"))})
    for fields in CV_PROJECTS:
        CvProject.objects.create(**{**fields, "write_up": projects.get(fields.get("write_up"))})
    for group_position, (title, skills) in enumerate(SKILLS):
        group = SkillGroup.objects.create(title=title, position=group_position)
        for skill_position, (name, evidence) in enumerate(skills):
            skill = Skill.objects.create(group=group, name=name, position=skill_position)
            for position, (label, slug) in enumerate(evidence):
                Evidence.objects.create(
                    skill=skill, label=label, project=projects.get(slug), position=position
                )


class Migration(migrations.Migration):

    # The migrations this one replaces, which are on the live site already. Django
    # counts it as applied wherever all of them are.
    replaces = [
        ("cv", "0001_initial"),
        ("cv", "0002_from_my_cv"),
        ("cv", "0003_filled_in"),
        ("cv", "0004_more_entries"),
        ("cv", "0005_dates_and_skills"),
        ("cv", "0006_dissertation_link"),
        ("cv", "0007_coursework"),
        ("cv", "0008_competitions"),
    ]

    initial = True

    dependencies = [
        ("projects", "0001_squashed"),
    ]

    operations = [
        migrations.CreateModel(
            name="Profile",
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
                ("name", models.CharField(max_length=80)),
                (
                    "role",
                    models.CharField(
                        help_text='For example "Software developer · Glasgow".',
                        max_length=120,
                    ),
                ),
                (
                    "looking_for",
                    models.CharField(
                        help_text="What I'm looking for, on the ID card.",
                        max_length=200,
                    ),
                ),
                ("summary", models.TextField(help_text="The profile paragraph.")),
                ("github_url", models.URLField(blank=True, verbose_name="GitHub URL")),
                (
                    "linkedin_url",
                    models.URLField(blank=True, verbose_name="LinkedIn URL"),
                ),
                (
                    "updated",
                    models.DateField(
                        help_text="When the CV was last brought up to date."
                    ),
                ),
            ],
            options={
                "verbose_name": "profile",
            },
        ),
        migrations.CreateModel(
            name="Readout",
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
                ("value", models.CharField(max_length=40)),
                ("label", models.CharField(max_length=120)),
                ("position", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "ordering": ["position"],
            },
        ),
        migrations.CreateModel(
            name="Skill",
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
                ("name", models.CharField(max_length=80)),
                ("position", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "ordering": ["position"],
            },
        ),
        migrations.CreateModel(
            name="SkillGroup",
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
                ("title", models.CharField(max_length=60)),
                ("position", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "ordering": ["position"],
            },
        ),
        migrations.CreateModel(
            name="CvProject",
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
                ("title", models.CharField(max_length=120)),
                (
                    "meta",
                    models.CharField(
                        blank=True,
                        help_text='For example "MSc dissertation · 2025".',
                        max_length=60,
                    ),
                ),
                (
                    "stack",
                    models.CharField(
                        blank=True, help_text="Separated by commas.", max_length=200
                    ),
                ),
                ("summary", models.TextField(blank=True)),
                (
                    "points",
                    models.TextField(
                        blank=True,
                        help_text="Bullet points shown at first, one per line.",
                    ),
                ),
                (
                    "more_points",
                    models.TextField(
                        blank=True,
                        help_text='Bullet points under "More", one per line.',
                    ),
                ),
                ("is_key", models.BooleanField(default=False)),
                ("position", models.PositiveSmallIntegerField(default=0)),
                (
                    "write_up",
                    models.ForeignKey(
                        blank=True,
                        help_text="The project's write-up on the projects page, if it has one.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="projects.project",
                    ),
                ),
            ],
            options={
                "verbose_name": "CV project",
                "ordering": ["-is_key", "position"],
            },
        ),
        migrations.CreateModel(
            name="Entry",
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
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("education", "Education"),
                            ("experience", "Experience"),
                        ],
                        max_length=20,
                    ),
                ),
                ("title", models.CharField(max_length=120)),
                ("organisation", models.CharField(max_length=120)),
                (
                    "started",
                    models.CharField(
                        help_text='For example "Sep 2024".', max_length=20
                    ),
                ),
                (
                    "ended",
                    models.CharField(
                        blank=True,
                        help_text="Left empty while it's still going.",
                        max_length=20,
                    ),
                ),
                ("summary", models.TextField(blank=True)),
                (
                    "points",
                    models.TextField(
                        blank=True, help_text="Bullet points, one per line."
                    ),
                ),
                (
                    "more",
                    models.TextField(
                        blank=True,
                        help_text='Shown when "More" is opened, in Markdown. Empty means no "More".',
                    ),
                ),
                ("award", models.CharField(blank=True, max_length=160)),
                (
                    "position",
                    models.PositiveSmallIntegerField(
                        default=0, help_text="Lower numbers come first."
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        help_text='A project write-up to link to from "More".',
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="projects.project",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "entries",
                "ordering": ["kind", "position"],
            },
        ),
        migrations.CreateModel(
            name="Evidence",
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
                ("label", models.CharField(max_length=80)),
                ("position", models.PositiveSmallIntegerField(default=0)),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="projects.project",
                    ),
                ),
                (
                    "skill",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evidence",
                        to="cv.skill",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "evidence",
                "ordering": ["position"],
            },
        ),
        migrations.AddField(
            model_name="skill",
            name="group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="skills",
                to="cv.skillgroup",
            ),
        ),
        migrations.RunPython(fill_in, migrations.RunPython.noop),
    ]
