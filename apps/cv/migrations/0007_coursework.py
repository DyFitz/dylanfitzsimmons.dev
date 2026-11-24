import importlib

from django.db import migrations

# The MSc Software Development entry's "More", split into team projects and coursework, with
# the rest of the year's assignments added. Only replaced while it is still what the earlier
# migrations wrote, so an edit made in the admin is kept.
EARLIER = importlib.import_module("apps.cv.migrations.0004_more_entries")
LINK = importlib.import_module("apps.cv.migrations.0006_dissertation_link")

OLD = EARLIER.ENTRY_MORE["MSc Software Development"].replace(
    LINK.OLD.rstrip("\n"), LINK.NEW.rstrip("\n")
)

NEW = (
    "- Dissertation: Opus Equi, built from June to August 2025 "
    "([read it as a PDF](/static/files/opus-equi-dissertation.pdf)).\n"
    "\n"
    "**Team projects**\n"
    "\n"
    "- SRC Events, a team of three: an events platform for university societies. Responsible "
    "for the Django backend and its integration with the front end.\n"
    "- Turn-based strategy game in Java, a team of four: Scrum Master; designed the core "
    "architecture and wrote the enemy AI.\n"
    "- Software engineering, a team of six: Product Owner for a system to manage part-time "
    "teachers, written in Java. Prioritised the backlog, wrote user stories and planned three "
    "two-week iterations.\n"
    "- Enterprise cyber security, a team of five: a risk assessment of messaging apps "
    "(WhatsApp, Telegram and Signal) in a financial firm, using the ENISA framework against "
    "GDPR, DORA and MiFID II.\n"
    "\n"
    "**Coursework**\n"
    "\n"
    "- Advanced programming: a concurrent task runner in Java, with threads, cancellation and "
    "tasks that wait on others; the Composite pattern for a file system.\n"
    "- Algorithms and data structures: linked-list algorithms and set operations in Java.\n"
    "- Databases: normalisation to fourth normal form, and SQL including window functions.\n"
    "- Cyber security: an analysis of the 2024 Dell data breach, from the API weaknesses "
    "exploited to the company's response.\n"
    "- Systems and networks: assembly language for the Sigma16 architecture.\n"
    "- Programming: Connect Four in Java."
)


def revise(apps, schema_editor):
    Entry = apps.get_model("cv", "Entry")
    Entry.objects.filter(title="MSc Software Development", more=OLD).update(more=NEW)


class Migration(migrations.Migration):
    dependencies = [("cv", "0006_dissertation_link")]

    # Going back leaves the CV as it is: nothing here is needed for the site to work.
    operations = [migrations.RunPython(revise, migrations.RunPython.noop)]
