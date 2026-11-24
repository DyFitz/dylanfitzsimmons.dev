from django.db import migrations

# An outline for each project's write-up, so the page has its sections from the start. The
# text in square brackets is to be replaced, which can be done in the admin.
OUTLINE = """## What it does

[What {title} does and who it's for, in two or three sentences.]

## How it works

[The moving parts and how they fit together: a short paragraph or two.]

## Challenges

[One or two problems that were hard to solve, and how you solved them.]

## Results

[What it can do now, and how well. Real numbers make this section.]

- [A result worth pointing out]
- [Another one]

## What's next

[What you'd add or improve next, and anything you'd do differently if you started again.]
"""


def add_outlines(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    for project in Project.objects.filter(body=""):
        project.body = OUTLINE.format(title=project.title)
        project.save(update_fields=["body"])


def remove_outlines(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    for project in Project.objects.all():
        # Only an outline nobody has touched is taken away again.
        if project.body == OUTLINE.format(title=project.title):
            project.body = ""
            project.save(update_fields=["body"])


class Migration(migrations.Migration):
    dependencies = [("projects", "0002_first_projects")]

    operations = [migrations.RunPython(add_outlines, remove_outlines)]
