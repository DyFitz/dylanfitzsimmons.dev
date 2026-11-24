from django.db import migrations

# A link to the Opus Equi dissertation from the MSc Software Development entry.
OLD = "- Dissertation: Opus Equi, built from June to August 2025.\n"
NEW = (
    "- Dissertation: Opus Equi, built from June to August 2025 "
    "([read it as a PDF](/static/files/opus-equi-dissertation.pdf)).\n"
)


def revise(apps, schema_editor):
    Entry = apps.get_model("cv", "Entry")
    for entry in Entry.objects.filter(title="MSc Software Development", more__contains=OLD):
        entry.more = entry.more.replace(OLD, NEW)
        entry.save(update_fields=["more"])


class Migration(migrations.Migration):
    dependencies = [("cv", "0005_dates_and_skills"), ("projects", "0007_pinball_and_dissertation")]

    # Going back leaves the CV as it is: nothing here is needed for the site to work.
    operations = [migrations.RunPython(revise, migrations.RunPython.noop)]
