from django.db import migrations

# The months of the semester in Bucharest, and statsmodels added to Opus Equi's skills.


def revise(apps, schema_editor):
    Entry = apps.get_model("cv", "Entry")
    Evidence = apps.get_model("cv", "Evidence")
    Entry.objects.filter(
        organisation="University POLITEHNICA of Bucharest", started="2017", ended="2017"
    ).update(started="Feb 2017", ended="Jun 2017")
    Evidence.objects.filter(
        skill__name="NumPy, SciPy, statsmodels", label="NumPy, SciPy · Opus Equi"
    ).update(label="NumPy, SciPy, statsmodels · Opus Equi")


class Migration(migrations.Migration):
    dependencies = [("cv", "0004_more_entries"), ("projects", "0006_revisions")]

    # Going back leaves the CV as it is: nothing here is needed for the site to work.
    operations = [migrations.RunPython(revise, migrations.RunPython.noop)]
