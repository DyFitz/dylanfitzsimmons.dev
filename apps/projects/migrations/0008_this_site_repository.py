from django.db import migrations

# The write-up for this site links to its repository, now that the code is public. Left alone
# if a link has already been added in the admin.
REPOSITORY = "https://github.com/DyFitz/dylanfitzsimmons.dev"


def link_repository(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    Project.objects.filter(slug="this-site", repo_url="").update(repo_url=REPOSITORY)


class Migration(migrations.Migration):
    dependencies = [("projects", "0007_pinball_and_dissertation")]

    # Going back leaves the link in place: the write-up works with or without it.
    operations = [migrations.RunPython(link_repository, migrations.RunPython.noop)]
