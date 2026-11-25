"""Turns a Flex report into the weights and returns the site stores, and saves them.

Every figure is worked out in pounds, so a US holding's return includes the dollar's move
against the pound, as it does for the account. Then each is divided by the portfolio's value,
so no amount of money is kept.

A day's return is its closing value against the previous close plus any money paid in that
day, so deposits aren't counted as gains (a time-weighted return).
"""

from dataclasses import dataclass, field
from datetime import date

from django.db import transaction

from apps.investments.flex import Statement
from apps.investments.models import (
    Day,
    Holding,
    ImportRun,
    Income,
    Instrument,
    Portfolio,
    Price,
    PriceSeries,
    Trade,
)

# A rough region from the issuer's country, as a starting point to correct in the admin.
# Funds are registered in Ireland or Luxembourg whatever they hold, so they're left blank.
REGIONS = {
    "GB": "UK",
    "US": "US",
    "CA": "Americas",
    "JP": "Asia",
    "KR": "Asia",
    "TW": "Asia",
    "CN": "Asia",
    "HK": "Asia",
    "IN": "Asia",
    "AU": "Asia Pacific",
}
# Funds held only for their prices, to track a benchmark: marked so when they first appear.
# SSAC and ISAC are the same iShares MSCI ACWI fund in London, in pounds and in dollars.
BENCHMARK_FUNDS = {"SSAC": "acwi", "ISAC": "acwi"}
SERIES_NAMES = {
    "acwi": "World shares (iShares MSCI ACWI, accumulating)",
    "igls": "Short gilts (IGLS)",
    "erns": "Ultrashort sterling bonds (ERNS)",
    "sgln": "Gold (SGLN)",
    "semi": "Global semiconductors (SEMI)",
}
EUROPE = {"NL", "DE", "FR", "CH", "SE", "DK", "ES", "IT", "BE", "FI", "NO", "AT"}


class ImportRefusedError(ValueError):
    """The report can't be imported, e.g. it ends before the record starts."""


@dataclass
class Result:
    days: list[Day] = field(default_factory=list)
    holdings: list[tuple[int, Holding]] = field(default_factory=list)
    trades: list[tuple[int, Trade]] = field(default_factory=list)
    income: list[tuple[int | None, Income]] = field(default_factory=list)


def _region(country: str, kind: str) -> str:
    if "ETF" in kind or "ETC" in kind:
        return ""
    if country in EUROPE:
        return "Europe"
    return REGIONS.get(country, "")


def _units(statement: Statement, days: list[date]) -> dict[date, dict[int, float]]:
    """Units of each holding at each close, worked back from the end of the report.

    Working back from the closing positions, rather than forward from the first trade, keeps
    it right once the account is older than the report's window.
    """
    by_day: dict[date, dict[int, float]] = {}
    held = dict(statement.closing)
    trades = sorted(statement.trades, key=lambda trade: trade.day, reverse=True)
    i = 0
    for day in reversed(days):
        # Undo trades made after this close.
        while i < len(trades) and trades[i].day > day:
            trade = trades[i]
            held[trade.conid] = held.get(trade.conid, 0.0) - trade.quantity
            i += 1
        by_day[day] = {conid: units for conid, units in held.items() if abs(units) > 1e-9}
    return by_day


def build(statement: Statement, inception: date) -> Result:
    """Works out the weights and returns for every day in the report from the inception on."""
    days = sorted(day for day, value in statement.values.items() if value > 0)
    if not days or days[-1] < inception:
        raise ImportRefusedError("The report ends before the record starts.")
    units = _units(statement, days)

    flows: dict[date, float] = {}
    for item in statement.cash_items:
        if item.kind == "flow":
            flows[item.day] = flows.get(item.day, 0.0) + item.amount

    # The latest known price of each holding, carried over days its market was shut.
    price: dict[int, tuple[float, float]] = {}
    prices_on: dict[date, dict[int, tuple[float, float]]] = {}
    for (conid, day), quote in statement.prices.items():
        prices_on.setdefault(day, {})[conid] = quote
    trades_on: dict[date, list] = {}
    for trade in statement.trades:
        trades_on.setdefault(trade.day, []).append(trade)

    result = Result()
    bases: dict[date, float] = {}
    previous: date | None = None
    for day in days:
        before = dict(price)
        quotes = prices_on.get(day, {})
        price.update(quotes)
        for trade in trades_on.get(day, []):
            # A holding bought today has no daily price row until tomorrow, but the trade has
            # the close. Its rate is the rate at the time of the trade, near enough for a day.
            if trade.conid not in quotes:
                price[trade.conid] = (trade.close, trade.fx)

        value = statement.values[day]
        if day < inception:
            previous = day
            continue
        # What the day's return is measured against: the previous close plus money paid in.
        base = statement.values[previous] + flows.get(day, 0.0) if previous else 0.0
        first = day == inception or previous is None or previous < inception or base <= 0
        bases[day] = base if base > 0 else value
        result.days.append(
            Day(
                date=day,
                daily_return=0.0 if first else value / base - 1,
                cash_weight=statement.cash.get(day, 0.0) / value,
                flow=0.0 if first else flows.get(day, 0.0) / statement.values[previous],
            )
        )

        held_now = units[day]
        held_before = units[previous] if previous else {}
        for conid in held_now.keys() | held_before.keys():
            close, fx = price.get(conid, (0.0, 1.0))
            now = held_now.get(conid, 0.0)
            contribution = 0.0
            if not first:
                # The change in what was held at the last close, plus what today's trades made
                # or lost against today's close.
                old_close, old_fx = before.get(conid, (close, fx))
                carried = held_before.get(conid, 0.0) * (close * fx - old_close * old_fx)
                traded = sum(
                    t.quantity * close * fx - t.money * t.fx
                    for t in trades_on.get(day, [])
                    if t.conid == conid
                )
                contribution = (carried + traded) / base
            if now or contribution:
                result.holdings.append(
                    (
                        conid,
                        Holding(
                            date=day,
                            weight=now * close * fx / value,
                            contribution=contribution,
                            price=close,
                            fx=fx,
                        ),
                    )
                )

        for trade in trades_on.get(day, []):
            result.trades.append(
                (
                    trade.conid,
                    Trade(
                        ibkr_id=trade.ibkr_id,
                        date=day,
                        side=Trade.Side.BUY if trade.quantity > 0 else Trade.Side.SELL,
                        weight=abs(trade.money * trade.fx) / bases[day],
                    ),
                )
            )
        previous = day

    # Income counts on the first day with a value from when it was paid, measured like that
    # day's return, so the parts of a day's return add up to the whole.
    for item in statement.cash_items:
        on = next((day for day in bases if day >= item.day), None)
        if item.kind == "flow" or item.day < inception or on is None:
            continue
        result.income.append(
            (
                item.conid,
                Income(
                    ibkr_id=item.ibkr_id, date=on, kind=item.kind, weight=item.amount / bases[on]
                ),
            )
        )
    return result


def _instruments(statement: Statement) -> dict[int, Instrument]:
    """Adds anything new and refreshes IBKR's details. The admin's own fields are left alone."""
    found = {}
    for security in statement.securities.values():
        details = {
            "symbol": security.symbol,
            "name": security.name,
            "isin": security.isin,
            "currency": security.currency,
            "kind": security.kind,
            "exchange": security.exchange,
            "country": security.country,
        }
        series = BENCHMARK_FUNDS.get(security.symbol, "")
        instrument, created = Instrument.objects.get_or_create(
            conid=security.conid,
            defaults={
                **details,
                "region": _region(security.country, security.kind),
                "benchmark_only": bool(series),
                "series_key": series,
            },
        )
        if not created:
            for name, value in details.items():
                setattr(instrument, name, value)
            instrument.save()
        found[security.conid] = instrument
    return found


def _keep_prices(result: Result, instruments: dict[int, Instrument]) -> None:
    """Keeps the closes, in pounds, of holdings that have a price series."""
    for conid, holding in result.holdings:
        key = instruments[conid].series_key
        if not key or not holding.price:
            continue
        series, _ = PriceSeries.objects.get_or_create(
            key=key, defaults={"name": SERIES_NAMES.get(key, key), "source": "IBKR"}
        )
        Price.objects.update_or_create(
            series=series, date=holding.date, defaults={"close": holding.price * holding.fx}
        )


@transaction.atomic
def save(statement: Statement, source: str) -> ImportRun:
    """Stores a report. Importing the same days again replaces them, so it's safe to repeat."""
    portfolio = Portfolio.load()
    if portfolio is None:
        raise ImportRefusedError(
            "Set up the portfolio in the admin first, with its inception date."
        )
    result = build(statement, portfolio.inception)
    instruments = _instruments(statement)
    dates = [day.date for day in result.days]

    Day.objects.filter(date__in=dates).delete()
    Day.objects.bulk_create(result.days)
    Holding.objects.filter(date__in=dates).delete()
    for conid, holding in result.holdings:
        holding.instrument = instruments[conid]
    Holding.objects.bulk_create([holding for _, holding in result.holdings])
    _keep_prices(result, instruments)
    for conid, trade in result.trades:
        Trade.objects.update_or_create(
            ibkr_id=trade.ibkr_id,
            defaults={
                "date": trade.date,
                "instrument": instruments[conid],
                "side": trade.side,
                "weight": trade.weight,
            },
        )
    for conid, income in result.income:
        Income.objects.update_or_create(
            ibkr_id=income.ibkr_id,
            defaults={
                "date": income.date,
                "instrument": instruments.get(conid) if conid else None,
                "kind": income.kind,
                "weight": income.weight,
            },
        )
    return ImportRun.objects.create(
        source=source,
        status=ImportRun.Status.OK,
        period_from=dates[0] if dates else None,
        period_to=dates[-1] if dates else None,
        days=len(dates),
    )
