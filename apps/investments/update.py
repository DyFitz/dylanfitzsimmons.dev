"""The daily update: the account from IBKR and SONIA from the Bank of England, plus prices
loaded by hand from CSV files. Each source is tried on its own, so one failing doesn't stop
the other, and every attempt is recorded as an ImportRun."""

from dataclasses import dataclass, field
from datetime import date, timedelta

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction

from apps.investments import sources
from apps.investments.flex import FlexError, parse
from apps.investments.importer import SERIES_NAMES, ImportRefusedError, save
from apps.investments.models import Holding, ImportRun, Portfolio, Price, PriceSeries

FLEX_SOURCE = "IBKR Flex Web Service"
SONIA_SOURCE = "Bank of England (SONIA)"
SONIA_NAME = "SONIA Compounded Index"
# The days before the token runs out on which a reminder goes out, so it isn't sent daily.
REMIND_AT = {30, 14, 7, 3, 1, 0}


@dataclass
class Outcome:
    done: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@transaction.atomic
def store_prices(
    key: str,
    rows: list[tuple[date, float]],
    *,
    source: str,
    name: str = "",
    scale: float | None = None,
) -> tuple[int, float]:
    """Adds or replaces a series' closes. Returns how many were stored and the scale used.

    Without a scale, prices that overlap those already kept are checked for pence against
    pounds and rescaled to match.
    """
    series, _ = PriceSeries.objects.get_or_create(
        key=key, defaults={"name": name or SERIES_NAMES.get(key, key), "source": source}
    )
    if scale is None:
        known = dict(series.prices.values_list("date", "close"))
        # Closes of a fund held under this key count too, from imports before it had a series.
        for held in Holding.objects.filter(instrument__series_key=key).exclude(date__in=known):
            known[held.date] = held.price * held.fx
        rows, scale = sources.match_units(rows, known)
    else:
        rows = [(day, close * scale) for day, close in rows]
    for day, close in rows:
        Price.objects.update_or_create(series=series, date=day, defaults={"close": close})
    return len(rows), scale


def _failed(source: str, error: Exception, outcome: Outcome) -> None:
    ImportRun.objects.create(source=source, status=ImportRun.Status.FAILED, message=str(error))
    outcome.failed.append(f"{source}: {error}")


def update_account(outcome: Outcome, **fetch) -> None:
    try:
        data = sources.fetch_flex_report(
            settings.IBKR_FLEX_TOKEN, settings.IBKR_FLEX_QUERY_ID, **fetch
        )
        run = save(parse(data), source=FLEX_SOURCE)
    except (sources.SourceError, FlexError, ImportRefusedError) as error:
        _failed(FLEX_SOURCE, error, outcome)
        return
    if run.days:
        outcome.done.append(
            f"Account: {run.days} days, {run.period_from:%d %b} to {run.period_to:%d %b %Y}."
        )
    else:
        outcome.done.append("Account: nothing new.")


def update_sonia(outcome: Outcome, **fetch) -> None:
    latest = Price.objects.filter(series__key="sonia").order_by("-date").first()
    portfolio = Portfolio.load()
    if latest:
        since = latest.date - timedelta(days=7)
    elif portfolio:
        since = portfolio.inception - timedelta(days=7)
    else:
        since = date.today() - timedelta(days=30)  # noqa: DTZ011 - a date, not a time
    try:
        rows = sources.fetch_sonia(since, **fetch)
    except sources.SourceError as error:
        _failed(SONIA_SOURCE, error, outcome)
        return
    count, _ = store_prices(
        "sonia", rows, source="Bank of England, IUDZOS2", name=SONIA_NAME, scale=1
    )
    ImportRun.objects.create(
        source=SONIA_SOURCE,
        status=ImportRun.Status.OK,
        period_from=rows[0][0],
        period_to=rows[-1][0],
        days=count,
    )
    outcome.done.append(f"SONIA: up to {rows[-1][0]:%d %b %Y}.")


def check_token(outcome: Outcome, today: date) -> None:
    """Warns as the IBKR token's end date comes near; a new one is made in the Client Portal."""
    expires = settings.IBKR_FLEX_TOKEN_EXPIRES
    if not expires:
        return
    try:
        ends = date.fromisoformat(expires)
    except ValueError:
        outcome.warnings.append(f"IBKR_FLEX_TOKEN_EXPIRES isn't a date: {expires!r}.")
        return
    left = (ends - today).days
    if left < 0 or left in REMIND_AT:
        when = "has expired" if left < 0 else f"expires in {left} days, on {ends:%d %b %Y}"
        outcome.warnings.append(
            f"The IBKR Flex token {when}. Make a new one in the Client Portal (Performance & "
            "Reports, Flex Queries, Flex Web Service) and update IBKR_FLEX_TOKEN and "
            "IBKR_FLEX_TOKEN_EXPIRES on Render."
        )


def report(outcome: Outcome) -> None:
    """Emails any failures or warnings."""
    if not (outcome.failed or outcome.warnings):
        return
    subject = "Portfolio update failed" if outcome.failed else "Portfolio update: a reminder"
    body = "\n\n".join([*outcome.failed, *outcome.warnings, *outcome.done])
    EmailMessage(
        subject=f"[dylanfitzsimmons.dev] {subject}",
        body=body,
        to=[settings.CONTACT_EMAIL],
    ).send()


def run(today: date, **fetch) -> Outcome:
    outcome = Outcome()
    update_account(outcome, **fetch)
    update_sonia(outcome, **{k: v for k, v in fetch.items() if k == "opener"})
    check_token(outcome, today)
    return outcome
