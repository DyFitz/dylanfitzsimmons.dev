from datetime import date
from typing import Any

import sentry_sdk
from django.core.management.base import BaseCommand, CommandError

from apps.investments import update
from config.sentry import UPDATE_MONITOR


class Command(BaseCommand):
    help = (
        "The daily update, run by the cron job: downloads the account's Flex report from IBKR "
        "and SONIA (the Bank of England's, by way of FRED), then emails any failure or token "
        "reminder."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        # Tells Sentry when each run starts and how it ends, so a run that fails or never
        # happens raises an alert. Does nothing when error tracking is off.
        with sentry_sdk.monitor(monitor_slug="update-investments", monitor_config=UPDATE_MONITOR):
            self.update()

    def update(self) -> None:
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
