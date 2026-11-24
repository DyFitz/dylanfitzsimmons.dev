import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("projects", "0004_details_from_cv"),
    ]

    operations = [
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80)),
                ("role", models.CharField(help_text='For example "Software developer · Glasgow".', max_length=120)),
                ("looking_for", models.CharField(help_text="What I'm looking for, on the ID card.", max_length=200)),
                ("summary", models.TextField(help_text="The profile paragraph.")),
                ("github_url", models.URLField(blank=True, verbose_name="GitHub URL")),
                ("linkedin_url", models.URLField(blank=True, verbose_name="LinkedIn URL")),
                ("updated", models.DateField(help_text="When the CV was last brought up to date.")),
            ],
            options={
                "verbose_name": "profile",
            },
        ),
        migrations.CreateModel(
            name="Readout",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("value", models.CharField(max_length=40)),
                ("label", models.CharField(max_length=120)),
                ("position", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "ordering": ["position"],
            },
        ),
        migrations.CreateModel(
            name="SkillGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=60)),
                ("position", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "ordering": ["position"],
            },
        ),
        migrations.CreateModel(
            name="Entry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("education", "Education"), ("experience", "Experience")], max_length=20)),
                ("title", models.CharField(max_length=120)),
                ("organisation", models.CharField(max_length=120)),
                ("started", models.CharField(help_text='For example "Sep 2024".', max_length=20)),
                ("ended", models.CharField(blank=True, help_text="Left empty while it's still going.", max_length=20)),
                ("summary", models.TextField(blank=True)),
                ("points", models.TextField(blank=True, help_text="Bullet points, one per line.")),
                ("more", models.TextField(blank=True, help_text='Shown when "More" is opened, in Markdown. Empty means no "More".')),
                ("award", models.CharField(blank=True, max_length=160)),
                ("position", models.PositiveSmallIntegerField(default=0, help_text="Lower numbers come first.")),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        help_text='A project write-up to link to from "More".',
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="projects.project",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "entries",
                "ordering": ["kind", "position"],
            },
        ),
        migrations.CreateModel(
            name="CvProject",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                ("meta", models.CharField(blank=True, help_text='For example "MSc dissertation · 2025".', max_length=60)),
                ("stack", models.CharField(blank=True, help_text="Separated by commas.", max_length=200)),
                ("summary", models.TextField(blank=True)),
                ("points", models.TextField(blank=True, help_text="Bullet points shown at first, one per line.")),
                ("more_points", models.TextField(blank=True, help_text='Bullet points under "More", one per line.')),
                ("is_key", models.BooleanField(default=False)),
                ("position", models.PositiveSmallIntegerField(default=0)),
                (
                    "write_up",
                    models.ForeignKey(
                        blank=True,
                        help_text="The project's write-up on the projects page, if it has one.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="projects.project",
                    ),
                ),
            ],
            options={
                "verbose_name": "CV project",
                "ordering": ["-is_key", "position"],
            },
        ),
        migrations.CreateModel(
            name="Skill",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80)),
                ("position", models.PositiveSmallIntegerField(default=0)),
                (
                    "group",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="skills", to="cv.skillgroup"),
                ),
            ],
            options={
                "ordering": ["position"],
            },
        ),
        migrations.CreateModel(
            name="Evidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("label", models.CharField(max_length=80)),
                ("position", models.PositiveSmallIntegerField(default=0)),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="projects.project",
                    ),
                ),
                (
                    "skill",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="evidence", to="cv.skill"),
                ),
            ],
            options={
                "verbose_name_plural": "evidence",
                "ordering": ["position"],
            },
        ),
    ]
