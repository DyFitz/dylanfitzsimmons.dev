import importlib

from django.db import migrations

# Earlier roles and a semester abroad, from LinkedIn, and the "More" sections rewritten as lists.
# As before, text is only replaced while it still holds what the last migration put there, so
# anything edited in the admin is kept. The downloadable PDF is unchanged.
EARLIER = importlib.import_module("apps.cv.migrations.0003_filled_in")

ENTRY_MORE = {
    "MSc Software Development": (
        "- Dissertation: Opus Equi, built from June to August 2025.\n"
        "- SRC Events, a team of three: an events platform for university societies. "
        "Responsible for the Django backend and its integration with the front end.\n"
        "- Turn-based strategy game in Java, a team of four: Scrum Master; designed the core "
        "architecture and wrote the enemy AI."
    ),
    "MSc Financial Economics": (
        "- Dissertation: Brexit and the efficiency of the foreign exchange market, for sterling "
        "against the euro and the US dollar.\n"
        "- Bloomberg Terminal and EViews for market data and econometrics."
    ),
    "Co-Founder and Software Developer": (
        "- A fintech startup making algorithmic trading tools easier for retail investors to "
        "use.\n"
        "- Proposed product: a drag-and-drop strategy builder, with blocks for market data, "
        "indicators, comparisons, logic and orders, plus tutorials and a broker connection.\n"
        "- Released an alpha Python library on PyPI for building, backtesting and evaluating "
        "strategies from reusable components.\n"
        "- Development ended before the visual platform was built, owing to time and funding."
    ),
}

NEW_ENTRIES = [
    {
        "kind": "education",
        "title": "European Project Semester (Erasmus exchange)",
        "organisation": "University POLITEHNICA of Bucharest",
        "started": "2017",
        "ended": "2017",
        "summary": (
            "Cross-discipline engineering project in a team of six students from across Europe: "
            "the research, design and construction of a 3D-printed prosthetic hand, using MATLAB."
        ),
        "award": "Grade: 100%",
        "position": 5,
    },
    {
        "kind": "experience",
        "title": "English Teacher",
        "organisation": "EF English First, Shanghai",
        "started": "Oct 2019",
        "ended": "Oct 2020",
        "summary": "Full-time English teacher.",
        "points": (
            "Planned lessons around grammar, writing structure and the language students need for "
            "study and work.\n"
            "Assessed ability through standardised testing, tracked each student's progress and "
            "reported back to parents."
        ),
        "position": 6,
    },
    {
        "kind": "experience",
        "title": "Mechanical Engineering Intern",
        "organisation": "Changzhou Xingyu Automotive Lighting Systems, China",
        "started": "Jul 2017",
        "ended": "Sep 2017",
        "summary": (
            "Material Science and Research department of a tier 1 automotive lighting supplier, "
            "whose clients include Toyota, BMW and Volkswagen."
        ),
        "points": (
            "Batch-tested supplier materials, including SABIC plastics, with tensile, shear, "
            "compression, fatigue and hardness tests, and thermal ageing to simulate long-term "
            "wear.\n"
            "Inspected LEDs for imperfections with a scanning electron microscope, and tested "
            "plastic coatings on headlight lenses.\n"
            "Presented findings to the research team weekly, and carried out quality checks with "
            "the factory attached to the research centre.\n"
            "Supported the research for the team leader's PhD thesis."
        ),
        "position": 7,
    },
]


def fill_in(apps, schema_editor):
    Entry = apps.get_model("cv", "Entry")
    CvProject = apps.get_model("cv", "CvProject")
    Evidence = apps.get_model("cv", "Evidence")

    for entry in Entry.objects.filter(title__in=ENTRY_MORE):
        if entry.more == EARLIER.ENTRY_MORE.get(entry.title):
            entry.more = ENTRY_MORE[entry.title]
            entry.save(update_fields=["more"])

    for fields in NEW_ENTRIES:
        same = Entry.objects.filter(title=fields["title"], organisation=fields["organisation"])
        if not same.exists():
            Entry.objects.create(**fields)

    CvProject.objects.filter(title="Turn-based strategy game", meta="team project").update(
        meta="team of 4"
    )
    Evidence.objects.filter(skill__name="JavaScript", label="University coursework").update(
        label="SRC Events"
    )


class Migration(migrations.Migration):
    dependencies = [("cv", "0003_filled_in")]

    # Going back leaves the CV as it is: nothing here is needed for the site to work.
    operations = [migrations.RunPython(fill_in, migrations.RunPython.noop)]
