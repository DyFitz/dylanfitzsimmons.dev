"""How the portfolio is measured: its benchmarks and why they were chosen, as a row of its own
under the other three. The rules' line about the benchmark moves into it. Only fills in what
hasn't been changed in the admin."""

from django.db import migrations, models

MEASURED = """\
The portfolio is judged against three benchmarks, each answering a different question.

- **The policy benchmark** holds the portfolio's own split between shares and defence, but \
passively: 75% world shares, with the remaining 25% in short gilts, ultrashort sterling bonds, \
gold and cash, reset each quarter. It is the main yardstick, because it isolates the active \
decisions: if the portfolio beats it, the chip thesis and the choice of income holdings added \
value over simply owning the same mix through index funds.
- **World shares** (MSCI ACWI) shows what the simplest global tracker would have returned, and \
so what the 25% held in defence costs in a rising market or saves in a falling one.
- **Global semiconductors** is the thesis's own sector. It separates the effect of picking \
particular chip companies from that of the sector moving as a whole.

All three are in pounds and include dividends, matching how the portfolio itself is measured. \
A US index or a conventional 60/40 mix would misjudge a sterling portfolio that holds gold and \
is spread across markets. The benchmarks were fixed on 25 November 2026, before the results \
were known, so they cannot be chosen after the fact to flatter them."""

OLD_RULE = (
    "\n- Judged against a sterling policy benchmark, set on 25 November 2026 and fixed from "
    "then on."
)


def forwards(apps, schema_editor):
    Portfolio = apps.get_model("investments", "Portfolio")
    for portfolio in Portfolio.objects.filter(measured=""):
        portfolio.measured = MEASURED
        portfolio.rules = portfolio.rules.removesuffix(OLD_RULE)
        portfolio.save(update_fields=["measured", "rules"])


def backwards(apps, schema_editor):
    Portfolio = apps.get_model("investments", "Portfolio")
    for portfolio in Portfolio.objects.filter(measured=MEASURED):
        if not portfolio.rules.endswith(OLD_RULE):
            portfolio.rules += OLD_RULE
            portfolio.save(update_fields=["rules"])


class Migration(migrations.Migration):
    dependencies = [("investments", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="portfolio",
            name="measured",
            field=models.TextField(
                blank=True,
                help_text="How it is measured: the benchmarks and why they were chosen, in "
                "Markdown. Shown across the full width, under the other three.",
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
