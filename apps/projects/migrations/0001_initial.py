from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=80)),
                ("slug", models.SlugField(unique=True)),
                ("summary", models.CharField(max_length=200)),
                ("stack", models.CharField(help_text="What it's built with, separated by commas, main one first.", max_length=200)),
                ("role", models.CharField(blank=True, max_length=120)),
                ("period", models.CharField(blank=True, help_text='For example "2024 – 2025".', max_length=40)),
                ("year", models.CharField(blank=True, help_text="The year shown in the list.", max_length=10)),
                ("status", models.CharField(blank=True, help_text='For example "In progress", "Complete", "Live" or "Archived".', max_length=30)),
                ("screen", models.CharField(choices=[("site", "A web page being drawn"), ("forecast", "A forecast chart"), ("backtest", "A backtest chart")], default="site", max_length=20)),
                ("body", models.TextField(blank=True, help_text="The write-up, in Markdown.")),
                ("repo_url", models.URLField(blank=True, verbose_name="repository URL")),
                ("position", models.PositiveSmallIntegerField(default=0, help_text="Lower numbers come first in the list.")),
                ("is_published", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["position", "title"],
            },
        ),
    ]
