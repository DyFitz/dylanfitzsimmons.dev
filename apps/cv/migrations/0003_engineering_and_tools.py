"""The mechanical engineering degree in full, the Erasmus project's tools, Connect Four and
EViews taken out, version control split between GitLab and GitHub, Figma and PowerShell where
they were used, the tools this site added (Cloudflare, Sentry, uv and Ruff, and web security),
and plainer wording in place of hyphenated compounds. Text already changed in the admin is left
alone, and nothing is added twice."""

import re

from django.db import migrations

# (model, lookup, field, before, after): changed only if it still reads "before".
TEXT = [
    ("Readout", {"position": 0}, "value", "MSc × 2 · BEng", "MSc ×2 · BEng"),
    (
        "Readout",
        {"position": 0},
        "label",
        "Software development, financial economics and engineering",
        "Software development, financial economics and mechanical engineering",
    ),
    (
        "Entry",
        {"title": "BEng (Hons) Mechanical and Power Plant Systems Engineering"},
        "summary",
        "Mechatronics, energy systems and computational methods; MATLAB for PID controller "
        "design and thermodynamic simulations.",
        "The engineering of power generation and its delivery to consumers: the thermodynamic "
        "analysis of turbines, three-phase motors and generators, and the transmission and "
        "distribution of electrical power. Control engineering formed the mechatronics "
        "component, from modelling dynamic systems with Laplace transforms to designing PID "
        "controllers in MATLAB.",
    ),
    (
        "Entry",
        {"title": "European Project Semester (Erasmus exchange)"},
        "summary",
        "Cross-discipline engineering project in a team of six students from across Europe: the "
        "research, design and construction of a 3D-printed prosthetic hand, using MATLAB.",
        "Interdisciplinary engineering project in a team of six students from across Europe: the "
        "research, design and construction of a prosthetic hand, modelled in SolidWorks, "
        "3D-printed, and driven by a PID controller programmed in MATLAB.",
    ),
    ("Skill", {"name": "Bloomberg Terminal, EViews"}, "name", None, "Bloomberg Terminal"),
    (
        "CvProject",
        {"title": "dylanfitzsimmons.dev: this site"},
        "stack",
        "Python / Django, PostgreSQL, JavaScript, CSS, Docker, GitHub Actions, Render",
        "Python / Django, PostgreSQL, JavaScript, CSS, Docker, GitHub Actions, Render, Sentry",
    ),
]

# Phrases reworded wherever they appear in entries and projects.
PHRASES = [
    ("Independent, protocol-driven casework", "Independent casework governed by clinical protocols"),
    (
        "Two quantile-based models (XGBoost with a custom pinball-loss objective,",
        "Two quantile regression models (XGBoost with a custom objective based on pinball loss,",
    ),
    ("all 5 must-haves", "all five essential requirements"),
    ("linked-list algorithms and set operations", "algorithms on linked lists, and set operations"),
    ("framework set-up, security", "configuring the framework, security"),
    ("Batch-tested supplier materials", "Tested batches of supplier materials"),
]
REWORDED = {"Entry": ["summary", "points", "more"], "CvProject": ["summary", "points", "more_points"]}

# Lines taken out of an entry's "more" text: (entry, line).
REMOVED_LINES = [
    ("MSc Software Development", "- Programming: Connect Four in Java."),
]
REPLACED_LINES = [
    (
        "MSc Financial Economics",
        "- Bloomberg Terminal and EViews for market data and econometrics.",
        "- Bloomberg Terminal for market data and analysis.",
    ),
]

# A skill's evidence, swapped for a new list if it still holds exactly the old one:
# skill, old labels, new (label, write-up's slug).
EVIDENCE = [
    (
        "Git",
        ["Every project"],
        [
            ("GitLab · Opus Equi", "opus-equi"),
            ("GitLab · strategy game", None),
            ("GitHub · this site", "this-site"),
            ("GitHub · SRC Events", None),
        ],
    ),
    (
        "Figma",
        ["Enular"],
        [("Enular", "enular"), ("Opus Equi", "opus-equi"), ("SRC Events", None)],
    ),
    (
        "PowerShell",
        ["University projects"],
        [("This site", "this-site"), ("Opus Equi", "opus-equi"), ("Strategy game", None)],
    ),
]

# New tools: skill, the skill it follows, and where it was used.
NEW_SKILLS = [
    ("Cloudflare", "Render", [("DNS for this site's domain", "this-site")]),
    (
        "Sentry",
        "Cloudflare",
        [("This site: error tracking and a monitor on the daily job", "this-site")],
    ),
    ("uv, Ruff", "Sentry", [("This site", "this-site")]),
    ("Web security", "REST APIs", [("This site: CSP, two-factor login, HSTS", "this-site")]),
]


def forwards(apps, schema_editor):
    Entry = apps.get_model("cv", "Entry")
    SkillGroup = apps.get_model("cv", "SkillGroup")
    Skill = apps.get_model("cv", "Skill")
    Evidence = apps.get_model("cv", "Evidence")
    Project = apps.get_model("projects", "Project")
    projects = {project.slug: project for project in Project.objects.all()}

    for model, lookup, field, before, after in TEXT:
        rows = apps.get_model("cv", model).objects.filter(**lookup)
        if before is not None:
            rows = rows.filter(**{field: before})
        rows.update(**{field: after})

    for model, fields in REWORDED.items():
        for row in apps.get_model("cv", model).objects.all():
            changed = []
            for field in fields:
                text = getattr(row, field)
                for old, new in PHRASES:
                    text = re.sub(r"\s+".join(map(re.escape, old.split())), lambda _: new, text)
                if text != getattr(row, field):
                    setattr(row, field, text)
                    changed.append(field)
            if changed:
                row.save(update_fields=changed)

    for title, line in REMOVED_LINES:
        for entry in Entry.objects.filter(title=title, more__contains=line):
            entry.more = "\n".join(x for x in entry.more.split("\n") if x != line)
            entry.save(update_fields=["more"])
    for title, before, after in REPLACED_LINES:
        for entry in Entry.objects.filter(title=title, more__contains=before):
            entry.more = entry.more.replace(before, after)
            entry.save(update_fields=["more"])

    for name, old, new in EVIDENCE:
        skill = Skill.objects.filter(name=name).first()
        if skill is None:
            continue
        if list(skill.evidence.order_by("position").values_list("label", flat=True)) != old:
            continue
        skill.evidence.all().delete()
        for i, (label, slug) in enumerate(new):
            Evidence.objects.create(skill=skill, label=label, project=projects.get(slug), position=i)

    tools = SkillGroup.objects.filter(title="Tools").first()
    if tools is None:
        return
    for name, after, evidence in NEW_SKILLS:
        if tools.skills.filter(name=name).exists():
            continue
        skills = list(tools.skills.order_by("position", "pk"))
        names = [skill.name for skill in skills]
        at = names.index(after) + 1 if after in names else len(skills)
        for i, skill in enumerate(skills):
            new_position = i + (i >= at)
            if skill.position != new_position:
                skill.position = new_position
                skill.save(update_fields=["position"])
        skill = Skill.objects.create(group=tools, name=name, position=at)
        for i, (label, slug) in enumerate(evidence):
            Evidence.objects.create(skill=skill, label=label, project=projects.get(slug), position=i)


class Migration(migrations.Migration):
    dependencies = [
        ("cv", "0002_this_site_and_finance_modules"),
        ("projects", "0001_squashed"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
