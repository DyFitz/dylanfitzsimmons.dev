import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Message",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("email", models.EmailField(max_length=254, verbose_name="reply-to address")),
                (
                    "reason",
                    models.CharField(
                        choices=[
                            ("job", "Job opportunity"),
                            ("project", "Project or freelance"),
                            ("other", "Something else"),
                        ],
                        default="job",
                        max_length=20,
                    ),
                ),
                ("body", models.TextField(verbose_name="message")),
                (
                    "sent_at",
                    models.DateTimeField(db_index=True, default=django.utils.timezone.now),
                ),
                (
                    "sender_hash",
                    models.CharField(blank=True, db_index=True, editable=False, max_length=64),
                ),
                (
                    "emailed",
                    models.BooleanField(
                        default=False,
                        help_text="Whether the email about it went out. It's saved either way.",
                    ),
                ),
            ],
            options={
                "ordering": ["-sent_at"],
            },
        ),
    ]
