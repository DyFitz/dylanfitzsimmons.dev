import importlib

from django.db import migrations

# Two competition placings added to the MSc Financial Economics entry's "More". Only replaced
# while it is still what the earlier migration wrote, so an edit made in the admin is kept.
EARLIER = importlib.import_module("apps.cv.migrations.0004_more_entries")

OLD = EARLIER.ENTRY_MORE["MSc Financial Economics"]
NEW = OLD + (
    "\n- 2nd place, GUTIC Stock Pitch (Glasgow University Trading and Investment Club, "
    "Feb 2019), in a team of two: a pitch on BMW Group to judges from firms including KPMG and "
    "Smith & Williamson.\n"
    "- 2nd place and the prize for best presentation slides, ASES & GUCS Business Case "
    "Competition (Jan 2019): presented at the Grosvenor Hilton, Glasgow, to nine judges and "
    "around 120 guests."
)


def revise(apps, schema_editor):
    Entry = apps.get_model("cv", "Entry")
    Entry.objects.filter(title="MSc Financial Economics", more=OLD).update(more=NEW)


class Migration(migrations.Migration):
    dependencies = [("cv", "0007_coursework")]

    # Going back leaves the CV as it is: nothing here is needed for the site to work.
    operations = [migrations.RunPython(revise, migrations.RunPython.noop)]
