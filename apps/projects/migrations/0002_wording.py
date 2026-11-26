"""Plainer wording in the project summaries and write-ups, in place of hyphenated compounds.
Each phrase is replaced only where it still appears, so text rewritten in the admin is left
alone. Line breaks inside a phrase are allowed for."""

import re

from django.db import migrations

PHRASES = [
    (
        "a daily-reported investment portfolio",
        "an investment portfolio reported each trading day",
    ),
    ("behind a bot-detection script", "behind a bot detection script"),
    ("hand-written CSS", "CSS written by hand"),
    ("a keyboard-driven terminal view", "a terminal view operated from the keyboard"),
    ("the stress-test sliders", "the stress test sliders"),
    (
        "that the browser was re-blurring on every frame",
        "that the browser blurred again on every frame",
    ),
    ("pre-rendered shadow images", "shadow images rendered in advance"),
    ("a two-step HTTP API", "an HTTP API that works in two steps"),
    ("a world-shares fund", "a fund tracking world shares"),
    ("ten single-use backup codes", "ten backup codes, each valid once"),
    ("the signed-in user", "the user who is signed in"),
    (
        "a custom pinball-loss objective, which weights over- and under-prediction differently",
        "a custom objective based on pinball loss, which penalises forecasts that are too high "
        "and too low by different amounts",
    ),
    ("all 5 must-haves", "all five essential requirements"),
    ("a true-or-false signal", "a Boolean (true or false) signal"),
    ("true-or-false signals", "Boolean signals"),
    ("fast and slow moving-average periods", "periods for the fast and slow moving averages"),
    (
        "the community-maintained continuation of Backtrader",
        "the continuation of Backtrader maintained by its community",
    ),
    ("before the no-code platform", "before the visual platform, which needed no programming,"),
    ("Short user-testing sessions", "Short sessions of user testing"),
]


def reword(text: str, phrases=PHRASES) -> str:
    for old, new in phrases:
        text = re.sub(r"\s+".join(map(re.escape, old.split())), lambda _: new, text)
    return text


def forwards(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    for project in Project.objects.all():
        summary, body = reword(project.summary), reword(project.body)
        if (summary, body) != (project.summary, project.body):
            project.summary, project.body = summary, body
            project.save(update_fields=["summary", "body"])


class Migration(migrations.Migration):
    dependencies = [("projects", "0001_squashed")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
