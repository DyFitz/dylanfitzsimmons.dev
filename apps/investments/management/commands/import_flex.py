from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.investments.flex import FlexError, parse
from apps.investments.importer import ImportRefusedError, save
from apps.investments.models import ImportRun


class Command(BaseCommand):
    help = (
        "Import an IBKR Activity Flex report (XML). Only weights and returns are stored. "
        "Importing the same days again replaces them."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("path", type=Path, help="The downloaded report.")

    def handle(self, *args: Any, **options: Any) -> None:
        path: Path = options["path"]
        try:
            statement = parse(path.read_bytes())
            run = save(statement, source=path.name)
        except (OSError, FlexError, ImportRefusedError) as error:
            ImportRun.objects.create(
                source=path.name, status=ImportRun.Status.FAILED, message=str(error)
            )
            raise CommandError(str(error)) from error
        if not run.days:
            self.stdout.write("Nothing to import: the report ends before the record starts.")
            return
        self.stdout.write(
            f"Imported {run.days} day{'' if run.days == 1 else 's'}, "
            f"{run.period_from:%d %b %Y} to {run.period_to:%d %b %Y}."
        )
