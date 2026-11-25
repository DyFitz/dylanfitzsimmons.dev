from datetime import date
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.investments import update


class Command(BaseCommand):
    help = (
        "The daily update, run by the cron job: downloads the account's Flex report from IBKR "
        "and SONIA from the Bank of England, then emails any failure or token reminder."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        outcome = update.run(date.today())  # noqa: DTZ011 - a date, not a time
        for line in outcome.done:
            self.stdout.write(line)
        for line in outcome.warnings:
            self.stderr.write(line)
        try:
            update.report(outcome)
        except OSError as error:
            self.stderr.write(f"Couldn't send the email: {error}")
        if outcome.failed:
            raise CommandError("\n".join(outcome.failed))
