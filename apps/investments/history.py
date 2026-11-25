"""Loads what the importer stored into lined-up daily series for the maths.

`dates[0]` is the inception close. Daily series have one figure for each close after it:
`returns[t]` is the move from `dates[t]` to `dates[t + 1]`. Weights are at each close, so
`weights[t]` is what was held going into `returns[t]`.
"""

from dataclasses import dataclass, field
from datetime import date
from itertools import pairwise

from django.conf import settings

from apps.investments.analytics import TRADING_DAYS, policy_returns
from apps.investments.models import Day, Holding, Income, Instrument, Price, PriceSeries, Trade

# The policy benchmark from the investment rationale of 25 November 2026: a passive version of
# the portfolio's 75 / 25 split, reset to these weights at each quarter's end. Each part is a
# price series; for a fund the portfolio holds, IBKR's prices are used on the days it was held,
# and the series fills in the rest (the funds were bought the day after the inception).
POLICY = {"acwi": 0.75, "igls": 0.05, "erns": 0.05, "sgln": 0.10, "sonia": 0.05}
HELD = {"igls": "IGLS", "erns": "ERNS", "sgln": "SGLN"}
BENCHMARKS = {
    "policy": ("75/25", "Policy benchmark"),
    "acwi": ("ACWI", "World shares"),
}
CHIPS = "Semiconductors"
CHIPS_FUND = "SEMI"


@dataclass
class Line:
    """A holding over the history."""

    instrument: Instrument
    weights: list[float]  # at each close, 0 when not held
    returns: list[float | None]  # in pounds with dividends, None on days it wasn't held
    contributions: list[float]  # points of the portfolio's daily return, dividends included

    @property
    def details(self) -> dict:
        i = self.instrument
        return {"symbol": i.symbol, "sector": i.sector, "sleeve": i.sleeve, "region": i.region}


@dataclass
class History:
    dates: list[date]
    returns: list[float]
    cash: list[float]
    lines: dict[str, Line]
    risk_free: list[float]
    risk_free_source: str
    benchmarks: dict[str, list[float]] = field(default_factory=dict)
    trades: list[Trade] = field(default_factory=list)
    income: list[float] = field(default_factory=list)  # interest and fees, by day

    @property
    def days(self) -> int:
        """Trading days since the inception close."""
        return len(self.returns)


def _levels(series: list[tuple[date, float]], dates: list[date]) -> list[float] | None:
    """A price series' level at each date, carried over days it has none. None if it doesn't
    reach back to the first date."""
    if not series or series[0][0] > dates[0]:
        return None
    out, i, level = [], 0, series[0][1]
    for day in dates:
        while i < len(series) and series[i][0] <= day:
            level = series[i][1]
            i += 1
        out.append(level)
    return out


def _moves(levels: list[float]) -> list[float]:
    return [b / a - 1 for a, b in pairwise(levels)]


def load() -> History | None:
    days = list(Day.objects.order_by("date"))
    if not days:
        return None
    dates = [d.date for d in days]
    index = {day: i for i, day in enumerate(dates)}
    n = len(dates)

    by_instrument: dict[int, dict[int, Holding]] = {}
    # Funds held only to track a benchmark stay off the page; their tiny weight is left in
    # "cash and costs".
    held = Holding.objects.filter(date__in=dates, instrument__benchmark_only=False)
    for h in held.select_related("instrument"):
        by_instrument.setdefault(h.instrument_id, {})[index[h.date]] = h
    paid: dict[tuple[int, int], float] = {}
    other_income = [0.0] * n
    for item in Income.objects.filter(date__in=dates).exclude(instrument__benchmark_only=True):
        if item.instrument_id and item.kind in ("dividend", "tax"):
            key = (item.instrument_id, index[item.date])
            paid[key] = paid.get(key, 0.0) + item.weight
        else:
            other_income[index[item.date]] += item.weight

    lines = {}
    for instrument in Instrument.objects.filter(pk__in=by_instrument):
        held = by_instrument[instrument.pk]
        weights = [held[t].weight if t in held else 0.0 for t in range(n)]
        returns: list[float | None] = []
        contributions = []
        for t in range(1, n):
            before, now = held.get(t - 1), held.get(t)
            dividend = paid.get((instrument.pk, t), 0.0)
            contributions.append((now.contribution if now else 0.0) + dividend)
            if before and now and before.weight:
                price = (now.price * now.fx) / (before.price * before.fx) - 1
                # Income is measured against the previous close plus any money paid in.
                returns.append(price + dividend * (1 + days[t].flow) / before.weight)
            else:
                returns.append(None)
        lines[instrument.symbol] = Line(instrument, weights, returns, contributions)

    sonia = _series("sonia", dates, accrues=True)
    if sonia:
        risk_free, source = sonia, "SONIA"
    else:
        daily = (1 + settings.INVESTMENTS_RISK_FREE) ** (1 / TRADING_DAYS) - 1
        risk_free = [daily] * (n - 1)
        source = f"{settings.INVESTMENTS_RISK_FREE:.1%} a year"

    history = History(
        dates=dates,
        returns=[d.daily_return for d in days[1:]],
        cash=[d.cash_weight for d in days],
        lines=lines,
        risk_free=risk_free,
        risk_free_source=source,
        trades=list(
            Trade.objects.filter(date__in=dates, instrument__benchmark_only=False).select_related(
                "instrument"
            )
        ),
        income=other_income[1:],
    )
    history.benchmarks = _benchmarks(history)
    return history


def _accrue(prices: list[tuple[date, float]], dates: list[date]) -> list[tuple[date, float]]:
    """Carries an interest index past its last published day at its latest rate, so days
    still waiting for publication earn interest rather than none. The published figures
    replace these once they arrive."""
    if len(prices) < 2 or prices[-1][0] >= dates[-1]:
        return prices
    (before, low), (last, high) = prices[-2], prices[-1]
    daily = (high / low) ** (1 / max((last - before).days, 1))
    return prices + [(day, high * daily ** (day - last).days) for day in dates if day > last]


def _series(key: str, dates: list[date], *, accrues: bool = False) -> list[float] | None:
    series = PriceSeries.objects.filter(key=key).first()
    if series is None:
        return None
    prices = list(Price.objects.filter(series=series).order_by("date").values_list("date", "close"))
    if accrues:
        prices = _accrue(prices, dates)
    levels = _levels(prices, dates)
    return _moves(levels) if levels else None


def _held(history: History, symbol: str) -> list[float | None]:
    line = history.lines.get(symbol)
    return list(line.returns) if line else [None] * history.days


def _part(history: History, key: str) -> list[float] | None:
    """A benchmark part's daily returns, or None if any day is missing."""
    series = _series(key, history.dates)
    if key not in HELD:
        return series
    held = _held(history, HELD[key])
    merged = [h if h is not None else (series[t] if series else None) for t, h in enumerate(held)]
    return None if any(r is None for r in merged) else merged


def _benchmarks(history: History) -> dict[str, list[float]]:
    """The benchmarks the data allows. One with a missing part is left out, not guessed."""
    parts = {key: _part(history, key) for key in POLICY}
    out = {}
    if all(series is not None for series in parts.values()):
        out["policy"] = policy_returns(history.dates, parts, POLICY)
    if parts["acwi"] is not None:
        out["acwi"] = parts["acwi"]
    return out


def chips(history: History) -> tuple[int, list[float], list[float]] | None:
    """The chip holdings as one, weighted as held, against the chip fund on its own, from the
    first day the fund was held: (index of that day, the holdings, the fund)."""
    fund = _held(history, CHIPS_FUND)
    start = next((t for t, r in enumerate(fund) if r is not None), None)
    picks = [line for line in history.lines.values() if line.instrument.sector == CHIPS]
    if start is None or not picks or any(r is None for r in fund[start:]):
        return None
    sleeve = []
    for t in range(start, history.days):
        weight = sum(line.weights[t] for line in picks)
        made = sum(line.contributions[t] for line in picks)
        sleeve.append(made / weight if weight else 0.0)
    return start, sleeve, [r for r in fund[start:] if r is not None]
