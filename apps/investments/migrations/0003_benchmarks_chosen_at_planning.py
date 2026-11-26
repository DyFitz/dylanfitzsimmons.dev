"""When the benchmarks were set (while the portfolio was planned, before its first trade), and
plainer wording in place of hyphenated compounds. Only text that still reads as it did is
changed, so edits made in the admin are left alone."""

import re

from django.db import migrations

OLD = (
    "The benchmarks were fixed on 25 November 2026, before the results were known, so they "
    "cannot be chosen after the fact to flatter them."
)
NEW = (
    "The benchmarks were set when the portfolio was planned, before its first trade in "
    "October 2026, and are kept fixed."
)


# Phrases reworded in the thesis, the holdings and the rules.
PHRASES = [
    ("Dividend-paying businesses", "Businesses that pay dividends"),
    ("data-centre power", "power for data centres"),
    ("reset at each quarter-end", "reset at the end of each quarter"),
]
SECTOR = ("Data-centre power", "Power for data centres")


def replace(apps, old: str, new: str) -> None:
    Portfolio = apps.get_model("investments", "Portfolio")
    for portfolio in Portfolio.objects.filter(measured__contains=old):
        portfolio.measured = portfolio.measured.replace(old, new)
        portfolio.save(update_fields=["measured"])


def forwards(apps, schema_editor):
    replace(apps, OLD, NEW)

    Portfolio = apps.get_model("investments", "Portfolio")
    for portfolio in Portfolio.objects.all():
        changed = []
        for field in ("idea", "holdings", "rules"):
            text = getattr(portfolio, field)
            for old, new in PHRASES:
                text = re.sub(r"\s+".join(map(re.escape, old.split())), lambda _, n=new: n, text)
            if text != getattr(portfolio, field):
                setattr(portfolio, field, text)
                changed.append(field)
        if changed:
            portfolio.save(update_fields=changed)
    apps.get_model("investments", "Instrument").objects.filter(sector=SECTOR[0]).update(
        sector=SECTOR[1]
    )


def backwards(apps, schema_editor):
    replace(apps, NEW, OLD)


class Migration(migrations.Migration):
    dependencies = [("investments", "0002_how_it_is_measured")]

    operations = [migrations.RunPython(forwards, backwards)]
