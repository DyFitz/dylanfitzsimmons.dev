"""This site as a key project under Opus Equi, the finance modules on the MSc, and the skills
the site has shown: Docker, CI, testing, REST APIs and the front end. Text already changed in
the admin is left alone, and nothing is added twice."""

from django.db import migrations

THIS_SITE = {
    "title": "dylanfitzsimmons.dev: this site",
    "meta": "Personal project · 2026",
    "stack": "Python / Django, PostgreSQL, JavaScript, CSS, Docker, GitHub Actions, Render",
    "points": (
        "A production Django site for projects, a CV, a contact form and a live investment "
        "portfolio: server-rendered pages that work without JavaScript, under a strict Content "
        "Security Policy.\n"
        "A scheduled data pipeline: a Render cron job collects the brokerage account from "
        "Interactive Brokers' Flex Web Service each weekday, reduces it to time-weighted "
        "returns and weights, and emails the reason when anything fails."
    ),
    "more_points": (
        "Portfolio analytics (Sharpe and Sortino ratios, drawdowns, risk contributions, a "
        "Monte Carlo projection and stress tests) computed in Python on the server and mirrored "
        "in JavaScript, the two agreeing to within floating-point rounding.\n"
        "Around 300 automated tests at 97% coverage, with linting, migration checks and a PostgreSQL "
        "test run in GitHub Actions on every push, shipped as a multi-stage Docker image."
    ),
    "is_key": True,
    "position": 1,
}

FINANCE_TITLE = "MSc Financial Economics"
FINANCE_BEFORE = (
    "Asset pricing, mathematical finance and computational finance. Coursework in C++ "
    "(stochastic calculus for options) and MATLAB (nonlinear volatility models)."
)
FINANCE_AFTER = (
    "Modules included C++ in Finance and Applied Mathematical Finance, alongside asset pricing "
    "and computational finance. Coursework in C++ (stochastic calculus for options) and MATLAB "
    "(nonlinear volatility models)."
)
CPP_BEFORE = "MSc Financial Economics: options pricing"
CPP_AFTER = "MSc Financial Economics: C++ in Finance, options pricing"

# Group, skill, the skill it follows (None for the end), and where it was used:
# (label, write-up's slug).
NEW_SKILLS = [
    ("Languages", "HTML and CSS", "JavaScript", [("This site", "this-site")]),
    (
        "Frameworks and libraries",
        "pytest, MSTest",
        None,
        [("pytest · this site", "this-site"), ("pytest, MSTest · Opus Equi", "opus-equi")],
    ),
    ("Tools", "Docker", "Git", [("This site: a multi-stage production image", "this-site")]),
    (
        "Tools",
        "GitHub Actions",
        "Docker",
        [("This site: tests and checks on every push", "this-site")],
    ),
    (
        "Tools",
        "REST APIs",
        None,
        [
            ("A FastAPI service · Opus Equi", "opus-equi"),
            ("IBKR's Flex Web Service · this site", "this-site"),
        ],
    ),
]
# Render was already listed, for SRC Events; this site goes first.
RENDER_EVIDENCE = ("This site: web service and cron job", "this-site")


def forwards(apps, schema_editor):
    CvProject = apps.get_model("cv", "CvProject")
    Entry = apps.get_model("cv", "Entry")
    SkillGroup = apps.get_model("cv", "SkillGroup")
    Skill = apps.get_model("cv", "Skill")
    Evidence = apps.get_model("cv", "Evidence")
    Project = apps.get_model("projects", "Project")
    projects = {project.slug: project for project in Project.objects.all()}

    # Key projects come first on the CV, so this one follows Opus Equi.
    if not CvProject.objects.filter(title=THIS_SITE["title"]).exists():
        CvProject.objects.create(**THIS_SITE, write_up=projects.get("this-site"))

    Entry.objects.filter(title=FINANCE_TITLE, summary=FINANCE_BEFORE).update(summary=FINANCE_AFTER)
    Evidence.objects.filter(label=CPP_BEFORE).update(label=CPP_AFTER)

    groups = {group.title: group for group in SkillGroup.objects.all()}
    for group_title, name, after, evidence in NEW_SKILLS:
        group = groups.get(group_title)
        if group is None or group.skills.filter(name=name).exists():
            continue
        skills = list(group.skills.order_by("position", "pk"))
        names = [skill.name for skill in skills]
        at = names.index(after) + 1 if after in names else len(skills)
        for i, skill in enumerate(skills):
            new_position = i + (i >= at)
            if skill.position != new_position:
                skill.position = new_position
                skill.save(update_fields=["position"])
        skill = Skill.objects.create(group=group, name=name, position=at)
        for i, (label, slug) in enumerate(evidence):
            Evidence.objects.create(skill=skill, label=label, project=projects.get(slug), position=i)

    render = Skill.objects.filter(name="Render").first()
    label, slug = RENDER_EVIDENCE
    if render and not render.evidence.filter(label=label).exists():
        for item in render.evidence.order_by("-position"):
            item.position += 1
            item.save(update_fields=["position"])
        Evidence.objects.create(skill=render, label=label, project=projects.get(slug), position=0)


class Migration(migrations.Migration):
    dependencies = [
        ("cv", "0001_squashed"),
        ("projects", "0001_squashed"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
