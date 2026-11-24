import importlib

from django.db import migrations

# Opus Equi's pinball-loss challenge now says what goes wrong and what was done about it, and
# drops the claim about crossing quantiles, which the code doesn't do. The write-up also links
# to the dissertation. As before, a passage is only replaced while it is word for word what the
# last migration wrote.
EARLIER = importlib.import_module("apps.projects.migrations.0006_revisions")
DISSERTATION = "/static/files/opus-equi-dissertation.pdf"

REPLACEMENTS = [
    (
        EARLIER.REPLACEMENTS["opus-equi"][0][1],
        """The second was the quantile model. The XGBoost forecasts are trained on the pinball loss,
written as a custom objective. For a quantile level τ, the loss weights a forecast that falls
short by τ and one that overshoots by 1 − τ, so minimising it gives the τ-quantile of the
price rather than its mean.

The loss doesn't suit XGBoost as it stands. XGBoost sizes each step from the gradient divided
by the second derivative, the Hessian, and the pinball loss is made of straight lines, so its
second derivative is zero almost everywhere and the steps break down. The custom objective
returns the gradient, 1 − τ or −τ depending on which side of the price the forecast falls,
with a constant Hessian of 1, which keeps every step bounded and training stable.

The starting point needed the same care. XGBoost's default starting value is nowhere near a
commodity price, so the early rounds would be spent climbing towards it. Instead, each
quantile's booster starts from that quantile of the training prices. One booster is trained
for each quantile, at 5%, 50% and 95%, and the trained boosters are kept in a map keyed by
quantile.
""",
    ),
    (
        """It was built as the dissertation for the MSc in Software Development at the University of
Glasgow, over nine weeks between June and August 2025.
""",
        f"""It was built as the dissertation for the MSc in Software Development at the University of
Glasgow, over nine weeks between June and August 2025. The full dissertation is available to
read: [Opus Equi dissertation (PDF)]({DISSERTATION}).
""",
    ),
]


def revise(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    for project in Project.objects.filter(slug="opus-equi"):
        body = project.body
        for old, new in REPLACEMENTS:
            body = body.replace(old, new)
        if body != project.body:
            project.body = body
            project.save(update_fields=["body"])


class Migration(migrations.Migration):
    dependencies = [("projects", "0006_revisions")]

    # Going back leaves the text as it is: nothing here is needed for the site to work.
    operations = [migrations.RunPython(revise, migrations.RunPython.noop)]
