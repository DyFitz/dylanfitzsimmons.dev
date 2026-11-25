from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.investments.models import Holding, Price
from apps.investments.sources import read_prices
from apps.investments.update import store_prices


class Command(BaseCommand):
    help = (
        "Import daily closes from a CSV file into a price series, e.g. a benchmark's history "
        "from before its fund was bought. Takes a date column and a close or price column. "
        "London prices in pence are spotted from any days already kept, or use --pence."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("key", help="The series, e.g. acwi, igls, erns, sgln or semi.")
        parser.add_argument("path", type=Path, help="The CSV file.")
        parser.add_argument("--name", default="", help="A name, if the series is new.")
        units = parser.add_mutually_exclusive_group()
        units.add_argument("--pence", action="store_true", help="The prices are in pence.")
        units.add_argument("--pounds", action="store_true", help="The prices are in pounds.")

    def handle(self, *args: Any, **options: Any) -> None:
        path: Path = options["path"]
        try:
            rows = read_prices(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError) as error:
            raise CommandError(str(error)) from error
        if not rows:
            raise CommandError("No dates and prices found in the file.")
        scale = 0.01 if options["pence"] else 1.0 if options["pounds"] else None
        days = [day for day, _ in rows]
        overlap = (
            Price.objects.filter(series__key=options["key"], date__in=days).exists()
            or Holding.objects.filter(instrument__series_key=options["key"], date__in=days).exists()
        )
        if scale is None and not overlap:
            self.stderr.write(
                "None of these days are kept yet, so the units can't be checked: taken as "
                "pounds. Use --pence if they're in pence, or include a few recent days."
            )
        count, used = store_prices(
            options["key"], rows, source=path.name, name=options["name"], scale=scale
        )
        note = " (converted from pence)" if used == 0.01 else ""
        self.stdout.write(
            f"Stored {count} prices for {options['key']}, "
            f"{rows[0][0]:%d %b %Y} to {rows[-1][0]:%d %b %Y}{note}."
        )
