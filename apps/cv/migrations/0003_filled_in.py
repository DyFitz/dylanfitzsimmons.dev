import importlib

from django.db import migrations

# Fills in more of the text that was left in square brackets. Each field is only changed while
# it still holds what the first CV migration put there, so edits made in the admin are kept.
FIRST = importlib.import_module("apps.cv.migrations.0002_from_my_cv")

ENTRY_MORE = {
    "MSc Software Development": (
        "The dissertation, Opus Equi, was built over nine weeks from June to August 2025. Two "
        "team projects ran alongside the taught courses: SRC Events, an events platform for "
        "university societies, with responsibility for its Django backend; and a turn-based "
        "strategy game in Java, with responsibility for its core architecture and enemy AI. On "
        "SRC Events, when the front end and backend still weren't working together close to the "
        "deadline, the team was brought together for a working session that got the "
        "integration finished and the site working."
    ),
    "MSc Financial Economics": (
        "Hands-on work with Bloomberg Terminal and EViews alongside the C++ and MATLAB "
        "coursework. The course is the financial grounding behind later projects: Enular's "
        "strategy backtesting and the price forecasting in Opus Equi."
    ),
    "A&E Call Handler": (
        "The first point of contact for people calling 111, NHS 24's urgent care service for "
        "Scotland. Each call means capturing the caller's details and symptoms accurately and "
        "following the triage process, so that the call is passed to the right clinician, "
        "such as a nurse, pharmacist or dental nurse, or straight to the Scottish Ambulance "
        "Service when a life is at risk. The calls cover a wide range of conditions and need "
        "a calm, confident and empathetic manner throughout. The role has continued alongside "
        "full-time postgraduate study, and it carries over to software: staying calm under "
        "pressure, following a process exactly, and handing work on with clear records."
    ),
    "Co-Founder and Software Developer": (
        "Enular set out to make algorithmic trading tools easier for retail investors to use: "
        "buying shares had become straightforward, but testing a trading idea still took "
        "programming skills. Its proposed product was a drag-and-drop strategy builder, with "
        "blocks for market data, indicators, comparisons, logic and orders, tutorials, and a "
        "broker connection so that strategies could eventually place real orders. The public "
        "release was an alpha Python library on PyPI for building, backtesting and evaluating "
        "strategies from reusable components. Time and funding constraints ended development "
        "before the visual platform was built."
    ),
}

# The CV in the third person, without "I": the profile, two readouts and two projects.
PROFILE_SUMMARY = (
    "MSc Software Development graduate with a background in engineering and financial "
    "economics. Built Opus Equi, a desktop forecasting application with a C#/.NET 8 client over "
    "a Python FastAPI service, and took it from requirements through to unit, integration and "
    "acceptance testing. As co-founder of Enular, a fintech startup, designed the platform's "
    "backtesting engine and published it as a Python package on PyPI."
)
READOUT_LABELS = {
    "The languages I've built the most with": "The languages used most",
    "Best Student: the top Honours result in my year": (
        "Best Student: the top Honours result in the year"
    ),
}
PROJECT_SUMMARIES = {
    "SRC Events Management": (
        "An events platform for university societies. Responsible for the backend: framework "
        "set-up, security, authentication, the database layer and deployment on Render, with "
        "email through ProtonMail Bridge."
    ),
    "Turn-based strategy game": (
        "Designed the core architecture (game and turn managers, and the class hierarchy for "
        "units and cards) and wrote the enemy AI, with real-time updates over WebSockets."
    ),
}

# Where each skill was used, in place of the square brackets. A slug links to a write-up.
EVIDENCE = {
    ("JavaScript", "[where else]"): [("University coursework", None)],
    ("SQL", "[MySQL: where]"): [("MySQL · university coursework", None)],
    ("NumPy, SciPy, statsmodels", "[where used]"): [
        ("NumPy, SciPy · Opus Equi", "opus-equi"),
        ("statsmodels · Enular", "enular"),
    ],
    ("Bloomberg Terminal, EViews", "[where used]"): [("MSc Financial Economics", None)],
    ("PowerShell", "[where used]"): [("University projects", None)],
}
# Not used enough to list.
REMOVED_SKILLS = ["React"]

# "Calibrated" claimed more than was measured: how often real prices fall inside the interval
# was never tested on unseen data.
OPUS_POINTS = (
    "calibrated 5–95% prediction intervals",
    "5–95% prediction intervals",
)


def fill_in(apps, schema_editor):
    Entry = apps.get_model("cv", "Entry")
    CvProject = apps.get_model("cv", "CvProject")
    first_more = {entry["title"]: entry.get("more", "") for entry in FIRST.ENTRIES}
    for entry in Entry.objects.filter(title__in=ENTRY_MORE):
        if entry.more == first_more[entry.title]:
            entry.more = ENTRY_MORE[entry.title]
            entry.save(update_fields=["more"])

    Profile = apps.get_model("cv", "Profile")
    Profile.objects.filter(summary=FIRST.PROFILE["summary"]).update(summary=PROFILE_SUMMARY)
    Readout = apps.get_model("cv", "Readout")
    for old, new in READOUT_LABELS.items():
        Readout.objects.filter(label=old).update(label=new)
    first_summaries = {project["title"]: project.get("summary", "") for project in FIRST.PROJECTS}
    for title, summary in PROJECT_SUMMARIES.items():
        projects = CvProject.objects.filter(title=title, summary=first_summaries[title])
        projects.update(summary=summary)

    Skill = apps.get_model("cv", "Skill")
    Evidence = apps.get_model("cv", "Evidence")
    Project = apps.get_model("projects", "Project")
    write_ups = {project.slug: project for project in Project.objects.all()}
    for (skill_name, placeholder), replacements in EVIDENCE.items():
        for old in Evidence.objects.filter(skill__name=skill_name, label=placeholder):
            for offset, (label, slug) in enumerate(replacements):
                Evidence.objects.create(
                    skill=old.skill,
                    label=label,
                    project=write_ups.get(slug),
                    position=old.position + offset,
                )
            old.delete()
    for skill in Skill.objects.filter(name__in=REMOVED_SKILLS):
        # Only while it still has nothing but its placeholder.
        if set(skill.evidence.values_list("label", flat=True)) <= {"[where used]"}:
            skill.delete()

    first_points = {project["title"]: project.get("points", "") for project in FIRST.PROJECTS}
    for project in CvProject.objects.filter(write_up__slug="opus-equi"):
        if project.points == first_points.get(project.title):
            project.points = project.points.replace(*OPUS_POINTS)
            project.save(update_fields=["points"])


class Migration(migrations.Migration):
    dependencies = [("cv", "0002_from_my_cv"), ("projects", "0005_write_ups")]

    # Going back leaves the text as it is: nothing here is needed for the site to work.
    operations = [migrations.RunPython(fill_in, migrations.RunPython.noop)]
