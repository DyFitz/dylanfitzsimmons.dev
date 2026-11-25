"""Everything the investments page shows, worked out from the history and formatted.

The page is sent complete, for the period that suits the history's length, so it reads the
same with scripts off. Figures that need more history, or benchmark prices not yet loaded, are
shown as a dash with a note saying why.
"""

import math
from datetime import date, timedelta

from apps.investments import analytics as a
from apps.investments.charts import area_path, band_path, heat, line_path, tone, treemap
from apps.investments.history import BENCHMARKS, History, chips
from apps.investments.models import Instrument, Portfolio

PERIODS = [("1m", "1M"), ("3m", "3M"), ("ytd", "YTD"), ("1y", "1Y"), ("all", "All")]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SLEEVES = [*Instrument.Sleeve.choices, ("cash", "Cash")]
DASH = "\N{EN DASH}"
# Ratios that mean nothing over a month or two, so wait for three months.
SHORT_RATIOS = {
    "Return, annualised",
    "Sharpe ratio",
    "Sortino ratio",
    "Calmar ratio",
    "Alpha, annualised",
    "Information ratio",
    "Up capture",
    "Down capture",
    "Skew",
    "Excess kurtosis",
}
GLOSSARY = [
    (
        "Growth of 100",
        "What 100 put in at the start of the period would be now. It lets the portfolio and the "
        "benchmarks share one scale.",
    ),
    (
        "Benchmark",
        "What the portfolio is measured against. The main one is a passive version of its own "
        "75 / 25 split: world shares, short gilts, short sterling bonds, gold and cash, reset to "
        "those weights at each quarter's end.",
    ),
    (
        "Volatility",
        "How much the daily returns vary, scaled up to a year. Higher means a bumpier ride.",
    ),
    (
        "Drawdown",
        "A fall from the highest value reached so far. The worst one is the biggest loss anyone "
        "holding throughout would have sat through.",
    ),
    (
        "Sharpe ratio",
        "Return above what cash would have paid, divided by volatility. Above 1 is good.",
    ),
    ("Sortino ratio", "Like Sharpe, but only the falls count as risk."),
    ("Calmar ratio", "A year's return divided by the worst drawdown."),
    (
        "Beta",
        "How far the portfolio tends to move when the benchmark moves 1%. A beta of 1.2 means "
        "about 1.2%.",
    ),
    (
        "Alpha",
        "The return left over once beta has been accounted for: what the choice of holdings added.",
    ),
    ("Tracking error", "How far the portfolio strays from the benchmark, as a volatility."),
    ("Information ratio", "Return above the benchmark, per unit of tracking error."),
    (
        "Up and down capture",
        "The share of the benchmark's rising days, and of its falling days, that the portfolio "
        "caught.",
    ),
    ("VaR 95%", "Value at risk: a daily loss that is only beaten on about one day in twenty."),
    ("Expected shortfall", "The average loss on those worst one-in-twenty days."),
    (
        "Skew and kurtosis",
        "The shape of the daily returns: whether big moves lean one way, and how often extreme "
        "days turn up.",
    ),
    ("Correlation", "Whether two holdings move together, from -1 (opposite) to 1 (in step)."),
    (
        "Contribution",
        "A holding's weight times its return: how many points of the portfolio's return it "
        "supplied.",
    ),
    ("Risk share", "How much of the portfolio's volatility a holding is responsible for."),
    (
        "Effective holdings",
        "How many equal-sized holdings the portfolio behaves like. A few big positions pull it "
        "down.",
    ),
    ("Turnover", "How much of the portfolio was traded in a year, as a share of its value."),
    (
        "Sleeve",
        "One of the portfolio's four parts, each with its own job and target weight: growth, "
        "income and value, defensive equities, and capital defence.",
    ),
    (
        "Monte Carlo",
        "Hundreds of possible futures, made by replaying shuffled stretches of the portfolio's own "
        "past.",
    ),
    (
        "Stress test",
        "What a given fall would do to the portfolio at today's weights, with everything else "
        "held still.",
    ),
]


# ---------------------------------------------------------------- formatting


def pct(x: float | None, dp: int = 1, signed: bool = True) -> str:
    if x is None or not math.isfinite(x):
        return DASH
    # Rounded first, so a tiny loss doesn't show as "-0.0%".
    shown = round(x * 100, dp) + 0.0
    return f"{'+' if signed and shown > 0 else ''}{shown:.{dp}f}%"


def num(x: float | None, dp: int = 2) -> str:
    return DASH if x is None or not math.isfinite(x) else f"{x:.{dp}f}"


def long_date(day: date) -> str:
    return f"{day.day} {day:%b %Y}"


def weekdays_between(a_day: date, b_day: date) -> int:
    """Weekdays strictly after a_day and strictly before b_day."""
    count, day = 0, a_day + timedelta(days=1)
    while day < b_day:
        count += day.weekday() < 5
        day += timedelta(days=1)
    return count


# ---------------------------------------------------------------- the page


def build(history: History, portfolio: Portfolio, today: date) -> dict:
    """The page's figures. `today` decides whether the data is late."""
    n = history.days
    last = n  # index of the latest close
    dates = history.dates
    period = "1y" if a.period_ready("1y", n) else "all"
    period_label = dict(PERIODS)[period]
    start = a.period_start(dates, period, last)
    r = history.returns[start:]
    rf = history.risk_free[start:]
    bench_key = next((key for key in ("policy", "acwi") if key in history.benchmarks), None)
    b = history.benchmarks[bench_key][start:] if bench_key else None
    code, bench_name = BENCHMARKS[bench_key] if bench_key else (None, None)
    stats = a.stats(r, rf, b)
    whole = a.stats(history.returns, history.risk_free, history.benchmarks.get(bench_key))
    ratios = n >= a.NEED_RATIOS

    context = {
        "inception": long_date(dates[0]),
        "as_of": long_date(dates[-1]),
        "days": n,
        "period_label": period_label,
        "bench_code": code,
        "bench_name": bench_name,
        "risk_free": history.risk_free_source,
        "status": _status(dates[-1], today, n),
        "tiles": _tiles(whole, history, ratios, code),
    }
    context |= _growth(history, start, bench_key)
    context["returns"] = _returns_table(history, last)
    context |= _drawdowns(r)
    context |= _months(history)
    context |= _contributions(history, start)
    context |= _risk_and_holdings(history, start, period_label, b)
    context |= _allocation(history, portfolio)
    context |= _weights_over_time(history)
    context |= _trades(history)
    context["facts"] = _facts(stats, ratios)
    context["ratios_wait"] = None if ratios else _wait(n, a.NEED_RATIOS, "")
    context |= _rolling(history, bench_key)
    context |= _histogram(r, stats)
    context["correlation"] = _correlation(history, start)
    context |= _monte_carlo(history)
    context["scenarios"] = _scenarios(history)
    context["glossary"] = GLOSSARY
    context["data"] = payload(history, portfolio, context["status"])
    return context


def _asset(sector: str) -> str:
    if sector in ("Government bonds", "Short-term bonds"):
        return "Bonds"
    return "Gold" if sector == "Gold" else "Shares"


def payload(history: History, portfolio: Portfolio, status: dict) -> dict:
    """What the page's script needs to work everything out again, for any day and period.

    Like the stored figures, it holds weights and returns only, rounded to what the page shows.
    """

    def r(values, places=7):
        return [None if v is None else round(v, places) for v in values]

    index = {day: i for i, day in enumerate(history.dates)}
    targets = dict.fromkeys((key for key, _ in SLEEVES), 0.0)
    holdings = []
    for key, line in sorted(history.lines.items()):
        i = line.instrument
        sleeve = i.sleeve or "growth"
        if i.target_weight is not None:
            targets[sleeve] += float(i.target_weight) / 100
        holdings.append(
            {
                "ticker": key,
                "name": i.display_name,
                "sector": i.sector or "Other",
                "sleeve": sleeve,
                "region": i.region or "Other",
                "currency": i.currency,
                "asset": _asset(i.sector),
                "weights": r(line.weights),
                "returns": r(line.returns),
                "contributions": r(line.contributions),
            }
        )
    targets["cash"] = float(portfolio.cash_target) / 100
    grouped: dict[tuple[date, str], None] = {}
    for trade in history.trades:
        grouped.setdefault((trade.date, trade.instrument.symbol), None)
    first = history.dates[min(1, len(history.dates) - 1)]
    picks = chips(history)
    return {
        "dates": [d.isoformat() for d in history.dates],
        "returns": r(history.returns),
        "cash": r(history.cash),
        "riskFree": r(history.risk_free, 9),
        "riskFreeSource": history.risk_free_source,
        "benchmarks": [
            {"key": key, "code": code, "name": name, "returns": r(history.benchmarks[key])}
            for key, (code, name) in BENCHMARKS.items()
            if key in history.benchmarks
        ],
        "holdings": holdings,
        "targets": targets,
        "sleeves": [{"key": key, "name": name} for key, name in SLEEVES],
        "chips": {"start": picks[0], "sleeve": r(picks[1]), "fund": r(picks[2])} if picks else None,
        "trades": [
            {"day": index[day], "ticker": symbol} for day, symbol in sorted(grouped) if day in index
        ],
        "turnover": [
            {"day": index[t.date], "weight": round(t.weight, 7)}
            for t in history.trades
            if t.date > first and t.date in index
        ],
        "status": status,
        "glossary": [{"term": term, "text": text} for term, text in GLOSSARY],
    }


# The sector map is about 600 pixels wide on a computer, and its labels about 7.7 pixels a
# character, so a box's width in % says roughly how much of a label fits.
def _room(width_pct: float) -> int:
    return math.floor((width_pct * 6 - 14) / 7.7)


def _fits(text: str, width_pct: float) -> bool:
    return len(text) <= _room(width_pct)


def _fit(text: str, width_pct: float) -> str:
    room = _room(width_pct)
    if len(text) <= room:
        return text
    return text[: room - 1] + "…" if room >= 3 else ""


def _wait(n: int, need: int, what: str) -> dict:
    return {
        "text": f"{what} Day {n} of {need}.".strip(),
        "bar": f"{min(100, n / need * 100):.0f}%",
    }


def _status(last: date, today: date, n: int) -> dict:
    # The report for a day's close arrives the next morning, so one weekday behind is normal.
    missed = weekdays_between(last, today) - 1
    if missed >= 1:
        updates = "One daily update is" if missed == 1 else f"{missed} daily updates are"
        return {
            "late": True,
            "text": f"Out of date: the last close received was {long_date(last)}. {updates} "
            "missing, so everything here stops at that day.",
        }
    young = (
        f" Day {n} of the portfolio, so some figures are waiting for more history."
        if n < a.NEED_RATIOS
        else ""
    )
    return {"late": False, "text": f"Up to date: close of {long_date(last)}.{young}"}


def _tiles(s: a.Stats, history: History, ratios: bool, code: str | None) -> list[dict]:
    held = sum(1 for line in history.lines.values() if line.weights[-1] > 0)
    return [
        {
            "label": "Return",
            "value": pct(s.total),
            "cls": tone(s.total),
            "note": f"{pct(s.cagr)} a year" if s.cagr is not None else f"in {s.days} trading days",
        },
        {
            "label": "Volatility",
            "value": pct(s.vol, 1, False),
            "note": "annualised" if ratios else "annualised, early days",
        },
        {
            "label": "Sharpe ratio",
            "value": num(s.sharpe) if ratios else DASH,
            "note": f"risk-free {history.risk_free_source}"
            if ratios
            else f"after 3 months · day {history.days} of {a.NEED_RATIOS}",
        },
        {
            "label": "Worst fall",
            "value": pct(s.max_drawdown),
            "cls": "iv-down",
            "note": "from a peak",
        },
        {
            "label": "Beta",
            "value": num(s.beta),
            "note": f"to the {code} benchmark" if code else "once benchmark prices are in",
        },
        {
            "label": "Holdings",
            "value": str(held),
            "note": f"{pct(history.cash[-1], 1, False)} cash",
        },
    ]


def _growth(history: History, start: int, bench_key: str | None) -> dict:
    width, height = 1000, 300
    lines = [("port", "Portfolio", history.returns[start:])]
    for key, (series_code, _) in BENCHMARKS.items():
        if key in history.benchmarks:
            lines.append((key, series_code, history.benchmarks[key][start:]))
    values = [a.growth(series) for _, _, series in lines]
    flat = [v for series in values for v in series]
    lo, hi = min(flat), max(flat)
    pad = (hi - lo) * 0.08 or 1.0
    lo, hi = lo - pad, hi + pad
    drawn = []
    for (key, name, _), series in zip(lines, values, strict=True):
        drawn.append(
            {
                "key": key,
                "d": line_path(series, width, height, lo, hi),
                "label": f"{name} {pct(series[-1] / 100 - 1)}",
            }
        )
    dates = history.dates
    middle = (start + len(dates) - 1) // 2
    return {
        "growth_lines": drawn,
        "growth_area": area_path(drawn[0]["d"], width, height),
        # Five evenly spaced ticks, from the bottom up.
        "growth_ticks": [f"{lo + (hi - lo) * f:.0f}" for f in (0, 0.25, 0.5, 0.75, 1)],
        "growth_x": [long_date(dates[i]) for i in (start, middle, len(dates) - 1)],
    }


def _returns_table(history: History, last: int) -> dict:
    rows = [("port", "Portfolio", history.returns)]
    for key, (series_code, name) in BENCHMARKS.items():
        if key in history.benchmarks:
            rows.append((key, f"{series_code} · {name}", history.benchmarks[key]))
    picks = chips(history)
    if picks:
        offset, sleeve, fund = picks
        rows.append(("chips", "Chip holdings", [None] * offset + sleeve))
        rows.append(("semi", "SEMI · the chip fund", [None] * offset + fund))
    body = []
    for key, label, series in rows:
        cells = []
        for period, _ in PERIODS:
            s0 = a.period_start(history.dates, period, last)
            window = series[s0:]
            if not a.period_ready(period, history.days) or any(x is None for x in window):
                cells.append({"text": DASH, "cls": "iv-flat"})
            else:
                value = a.compound(window)
                cells.append({"text": pct(value), "cls": tone(value)})
        body.append({"key": key, "label": label, "cells": cells})
    return {"heads": [label for _, label in PERIODS], "rows": body}


def _drawdowns(r: list[float]) -> dict:
    falls = a.drawdowns(r)
    floor = min(-0.01, falls.worst * 1.1)
    width = 1000
    step = width / max(1, len(falls.series) - 1)
    path = "M0 0" + "".join(
        f"L{i * step:.1f} {v / floor * 120:.1f}" for i, v in enumerate(falls.series)
    )
    return {
        "dd_path": f"{path}L{width} 0Z",
        "dd_worst": pct(falls.worst),
        "dd_now": pct(falls.current),
    }


def _months(history: History) -> dict:
    months = a.monthly(history.dates[1:], history.returns)
    by_year: dict[int, dict[int, float]] = {}
    for year, month, value in months:
        by_year.setdefault(year, {})[month] = value
    years = []
    for year in sorted(by_year):
        cells, total = [], 1.0
        for month in range(1, 13):
            value = by_year[year].get(month)
            if value is None:
                cells.append(None)
            else:
                total *= 1 + value
                cells.append({"text": f"{value * 100:.1f}", "cls": heat(value, 0.08)})
        years.append(
            {"year": year, "cells": cells, "total": pct(total - 1), "cls": tone(total - 1)}
        )
    best = max(months, key=lambda m: m[2])
    worst = min(months, key=lambda m: m[2])

    def name(m):
        return f"{MONTHS[m[1] - 1]} {m[0]} {pct(m[2])}"

    return {
        "months": MONTHS,
        "years": years,
        "months_up": f"{sum(1 for m in months if m[2] > 0)} of {len(months)}",
        "best_month": name(best),
        "worst_month": name(worst),
    }


def _contributions(history: History, start: int) -> dict:
    parts = {key: line.contributions[start:] for key, line in history.lines.items()}
    totals, total = a.contributions(parts, history.returns[start:])
    other = totals.pop("other")
    rows = sorted(totals.items(), key=lambda kv: -kv[1])
    rows.append(("Cash and costs", other))
    widest = max((abs(v) for _, v in rows), default=0) or 1e-4
    return {
        "contributions": [
            {
                "name": name,
                "text": pct(v, 2).replace("%", " pts") if round(v * 100, 2) else "+0.00 pts",
                "cls": tone(v),
                # Half the track each way from the centre.
                "x": f"{50 if v >= 0 else 50 - abs(v) / widest * 50:.2f}%",
                "w": f"{abs(v) / widest * 50:.2f}%",
                "up": v >= 0,
            }
            for name, v in rows
        ],
        "contribution_total": pct(total, 2),
    }


def _holding_returns(history: History, key: str, s0: int) -> float | None:
    window = [x for x in history.lines[key].returns[s0:] if x is not None]
    return a.compound(window) if window else None


def _risk_and_holdings(history: History, start: int, period_label: str, b) -> dict:
    last = history.days
    r = history.returns[start:]
    weights = {key: line.weights[-1] for key, line in history.lines.items()}
    held = [key for key in weights if weights[key] > 0]
    returns = {key: history.lines[key].returns[start:] for key in held}
    shares = a.risk_shares({k: weights[k] for k in held}, returns, r)
    biggest_weight = max(weights.values(), default=0) or 1
    month_start = a.period_start(history.dates, "1m", last)
    ytd_start = a.period_start(history.dates, "ytd", last)
    rows = []
    for key in sorted(held, key=lambda k: -weights[k]):
        line = history.lines[key]
        mine = [x for x in line.returns[start:] if x is not None]
        day, month = line.returns[-1], _holding_returns(history, key, month_start)
        ytd, ret = _holding_returns(history, key, ytd_start), _holding_returns(history, key, start)
        beta = None
        if b is not None:
            x, y = a.paired(line.returns[start:], b)
            beta = a.beta(x, y) if len(x) > 1 else None
        rows.append(
            {
                "ticker": key,
                "name": line.instrument.display_name,
                "sector": line.instrument.sector or DASH,
                "weight": pct(weights[key], 1, False),
                "bar": f"{weights[key] / biggest_weight * 100:.1f}%",
                "cells": [
                    {"text": pct(day, 2), "cls": tone(day)},
                    {"text": pct(month), "cls": tone(month)},
                    {"text": pct(ytd), "cls": tone(ytd)},
                    {"text": pct(ret), "cls": tone(ret)},
                ],
                "beta": num(beta),
                "vol": pct(a.sd(mine) * math.sqrt(a.TRADING_DAYS), 0, False)
                if len(mine) > 1
                else DASH,
                "risk": pct(shares[key], 1, False),
            }
        )
    top = sorted(held, key=lambda k: -shares[k])[:10]
    scale = max([shares[k] for k in top] + [weights[k] for k in top] + [1e-4])
    return {
        "holdings": rows,
        "cash": pct(history.cash[-1], 1, False),
        "risk_bars": [
            {
                "ticker": k,
                "weight": pct(weights[k], 1, False),
                "risk": pct(shares[k], 1, False),
                "w": f"{weights[k] / scale * 100:.1f}%",
                "r": f"{max(0.0, shares[k]) / scale * 100:.1f}%",
            }
            for k in top
        ],
    }


def _allocation(history: History, portfolio: Portfolio) -> dict:
    weights = {key: line.weights[-1] for key, line in history.lines.items() if line.weights[-1]}
    # Each holding's return since the start, for the treemap's colours.
    returns = {key: _holding_returns(history, key, 0) or 0.0 for key in weights}
    sectors: dict[str, dict] = {}
    for key, weight in weights.items():
        sector = history.lines[key].instrument.sector or "Other"
        group = sectors.setdefault(sector, {"name": sector, "weight": 0.0, "made": 0.0})
        group["weight"] += weight
        group["made"] += weight * returns[key]
    if history.cash[-1] > 0.0005:
        sectors["Cash"] = {"name": "Cash", "weight": history.cash[-1], "made": 0.0}
    items = sorted(sectors.values(), key=lambda g: -g["weight"])
    tiles = []
    for box in treemap(
        [{"name": g["name"], "weight": g["weight"], "made": g["made"]} for g in items]
    ):
        ret = box["made"] / box["weight"] if box["weight"] else 0.0
        meta = f"{pct(box['weight'], 1, False)} · {pct(ret)}"
        tiles.append(
            {
                "name": _fit(box["name"], box["w"]),
                "full": f"{box['name']}: {meta}",
                "meta": _fit(meta, box["w"])
                if _fits(meta, box["w"])
                else pct(box["weight"], 1, False),
                "x": f"{box['x']:.3f}%",
                "y": f"{box['y']:.3f}%",
                "w": f"{box['w']:.3f}%",
                "h": f"{box['h']:.3f}%",
                "cls": heat(ret, 0.3),
                # Room for a second line of text.
                "big": box["h"] >= 14 and _fits(pct(box["weight"], 1, False), box["w"]),
            }
        )

    sleeves = []
    targets = {key: 0.0 for key, _ in SLEEVES}
    actual = {key: 0.0 for key, _ in SLEEVES}
    made = {key: 0.0 for key, _ in SLEEVES}
    for key, line in history.lines.items():
        sleeve = line.instrument.sleeve or "growth"
        if line.instrument.target_weight is not None:
            targets[sleeve] += float(line.instrument.target_weight) / 100
        actual[sleeve] += weights.get(key, 0.0)
        made[sleeve] += weights.get(key, 0.0) * returns.get(key, 0.0)
    targets["cash"] = float(portfolio.cash_target) / 100
    actual["cash"] = history.cash[-1]
    for key, label in SLEEVES:
        ret = made[key] / actual[key] if actual[key] and key != "cash" else None
        sleeves.append(
            {
                "name": label,
                "weight": pct(actual[key], 1, False),
                "target": pct(targets[key], 0, False),
                "bar": f"{min(100.0, actual[key] / 0.4 * 100):.1f}%",
                "mark": f"{min(100.0, targets[key] / 0.4 * 100):.1f}%",
                "ret": pct(ret),
                "cls": tone(ret),
            }
        )
    all_weights = [*weights.values(), history.cash[-1]]
    equities = sum(actual[k] for k in ("growth", "income", "defensive"))
    bonds = sum(
        weights[k]
        for k in weights
        if history.lines[k].instrument.sector in ("Government bonds", "Short-term bonds")
    )
    gold = sum(weights[k] for k in weights if history.lines[k].instrument.sector == "Gold")
    return {
        "tiles_map": tiles,
        "sleeves": sleeves,
        "asset_mix": f"{pct(equities, 0, False)} shares · {pct(bonds, 0, False)} bonds · "
        f"{pct(gold, 0, False)} gold · {pct(history.cash[-1], 0, False)} cash",
        "top5": pct(sum(sorted(weights.values())[-5:]), 0, False),
        "effective": f"{a.effective_holdings(all_weights):.1f}",
    }


def _weights_over_time(history: History) -> dict:
    n = len(history.dates)
    stacks = []
    for t in range(n):
        shares = dict.fromkeys((key for key, _ in SLEEVES), 0.0)
        for line in history.lines.values():
            shares[line.instrument.sleeve or "growth"] += line.weights[t]
        shares["cash"] = history.cash[t]
        stacks.append(shares)
    bands, below = [], [0.0] * n
    for key, label in SLEEVES:
        above = [below[t] + stacks[t][key] for t in range(n)]
        # Drawn from the top down, so 0 is the top of the box.
        bands.append(
            {
                "key": key,
                "name": label,
                "d": band_path([1 - v for v in above], [1 - v for v in below], 1000, 200),
            }
        )
        below = above
    return {
        "bands": bands,
        "bands_from": long_date(history.dates[0]),
        "bands_to": long_date(history.dates[-1]),
    }


def _trades(history: History) -> dict:
    """One row per holding a day, from its weight at the close before to the close after."""
    index = {day: i for i, day in enumerate(history.dates)}
    grouped: dict[tuple[date, str], bool] = {}
    for trade in history.trades:
        grouped.setdefault((trade.date, trade.instrument.symbol), trade.side == "buy")
    rows = []
    for (day, symbol), _bought in sorted(grouped.items(), key=lambda kv: kv[0][0], reverse=True):
        line = history.lines.get(symbol)
        if line is None:
            continue
        t = index[day]
        before = line.weights[t - 1] if t else 0.0
        after = line.weights[t]
        verb = (
            "Bought"
            if before == 0
            else "Sold"
            if after == 0
            else "Added to"
            if after > before
            else "Trimmed"
        )
        rows.append(
            {
                "date": long_date(day),
                "verb": verb,
                "buy": after >= before,
                "ticker": symbol,
                "name": line.instrument.display_name,
                "change": f"{pct(before, 1, False)} → {pct(after, 1, False)}",
            }
        )
    first = history.dates[min(1, len(history.dates) - 1)]
    later = [t for t in history.trades if t.date > first]
    year_ago = history.dates[-1] - timedelta(days=365)
    turned = a.turnover([t.weight for t in later if t.date > year_ago])
    return {
        "trades": rows[:8],
        "trade_count": f"{len(rows)} trade{'s' if len(rows) != 1 else ''}",
        "turnover": f"{pct(turned, 0, False)} of the portfolio traded in the last year"
        if later
        else "no trades since the first purchases",
    }


def _facts(s: a.Stats, ratios: bool) -> list[dict]:
    facts = [
        ("Return, annualised", pct(s.cagr) if s.cagr is not None else pct(s.annual) + "*"),
        ("Volatility", pct(s.vol, 1, False)),
        ("Sharpe ratio", num(s.sharpe)),
        ("Sortino ratio", num(s.sortino)),
        ("Calmar ratio", num(s.calmar)),
        ("Max drawdown", pct(s.max_drawdown)),
        ("Recovery", "not yet" if s.recovery_days is None else f"{s.recovery_days} days"),
        ("Current drawdown", pct(s.current_drawdown)),
        ("Beta", num(s.beta)),
        ("Alpha, annualised", pct(s.alpha)),
        ("Correlation", num(s.correlation)),
        ("Tracking error", pct(s.tracking_error, 1, False)),
        ("Information ratio", num(s.information_ratio)),
        ("Up capture", pct(s.up_capture, 0, False)),
        ("Down capture", pct(s.down_capture, 0, False)),
        ("VaR 95%, 1 day", pct(-s.var95, 2)),
        ("Expected shortfall 95%", pct(-s.cvar95, 2)),
        ("Best day", pct(s.best, 2)),
        ("Worst day", pct(s.worst, 2)),
        ("Positive days", pct(s.hit_rate, 0, False)),
        ("Skew", num(s.skew)),
        ("Excess kurtosis", num(s.kurtosis)),
    ]
    return [
        {"label": label, "value": DASH if not ratios and label in SHORT_RATIOS else value}
        for label, value in facts
    ]


def _rolling(history: History, bench_key: str | None) -> dict:
    n = history.days
    if n < a.NEED_ROLLING or bench_key is None:
        what = (
            "This needs four months of history: a three-month window, and a month of it moving."
            if n < a.NEED_ROLLING
            else "This needs the benchmark's prices, which aren't in yet."
        )
        return {"rolling": None, "rolling_wait": _wait(n, a.NEED_ROLLING, what)}
    points = a.rolling(history.returns, history.benchmarks[bench_key])
    vols = [v for _, v, _ in points]
    betas = [b for _, _, b in points]
    return {
        "rolling": {
            "vol": line_path(vols, 1000, 120, 0, max(vols) * 1.1),
            "beta": line_path(betas, 1000, 120, 0, max(2, *betas)),
            "vol_now": pct(vols[-1], 1, False),
            "beta_now": num(betas[-1]),
        },
        "rolling_wait": None,
    }


def _histogram(r: list[float], s: a.Stats) -> dict:
    width, bin_w, edge = 1000, 0.005, 0.06
    count = round(2 * edge / bin_w)
    bins = [0] * count
    for v in r:
        bins[min(count - 1, max(0, math.floor((v + edge) / bin_w)))] += 1
    m, sd = a.mean(r), a.sd(r) or 0.01
    curve_peak = bin_w * len(r) / (sd * math.sqrt(2 * math.pi))
    top = max(*bins, curve_peak, 1)
    slot = width / count
    bars = [
        {
            "x": f"{i * slot + 1:.1f}",
            "w": f"{slot - 2:.1f}",
            "y": f"{120 - c / top * 120:.1f}",
            "h": f"{c / top * 120:.1f}",
            "down": -edge + i * bin_w < 0,
        }
        for i, c in enumerate(bins)
        if c
    ]

    def normal(i: int) -> float:
        centre = -edge + (i + 0.5) * bin_w
        return curve_peak * math.exp(-(((centre - m) / sd) ** 2) / 2)

    curve = "".join(
        f"{'L' if i else 'M'}{(i + 0.5) * slot:.1f} {120 - normal(i) / top * 120:.1f}"
        for i in range(count)
    )
    return {"hist_bars": bars, "hist_curve": curve, "var95": pct(-s.var95, 2)}


def _correlation(history: History, start: int) -> dict:
    order = [
        key
        for key, line in sorted(
            history.lines.items(),
            key=lambda kv: (
                [s for s, _ in SLEEVES].index(kv[1].instrument.sleeve or "growth"),
                -kv[1].weights[-1],
            ),
        )
        if line.weights[-1] > 0
    ]
    series = {key: history.lines[key].returns[start:] for key in order}
    rows = []
    for key in order:
        cells = []
        for other in order:
            if key == other:
                value = 1.0
            else:
                x, y = a.paired(series[key], series[other])
                value = a.correlation(x, y)
            shown = round(value, 2) + 0.0
            text = "1" if shown == 1 else f"{shown:.2f}".replace("0.", ".", 1)
            cells.append({"text": text, "cls": heat(value, 1)})
        rows.append({"ticker": key, "cells": cells})
    return {"tickers": order, "rows": rows}


def _monte_carlo(history: History) -> dict:
    n = history.days
    if n < a.NEED_MONTE_CARLO:
        what = (
            "This needs six months of history. A projection built from less would only replay "
            "one kind of market."
        )
        return {"mc": None, "mc_wait": _wait(n, a.NEED_MONTE_CARLO, what)}
    years = 5
    projection = a.monte_carlo(history.returns, years)
    hi = max(projection.bands[-1][4], 1.2) * 1.05
    lo = min(*(b[0] for b in projection.bands), 0.9) * 0.95
    width, height = 1000, 300

    def y(v: float) -> float:
        return height - (math.log(v) - math.log(lo)) / (math.log(hi) - math.log(lo)) * height

    def band(low: int, high: int) -> str:
        step = width / (len(projection.bands) - 1)
        top = "".join(
            f"{'L' if i else 'M'}{i * step:.1f} {y(b[high]):.1f}"
            for i, b in enumerate(projection.bands)
        )
        bottom = "".join(
            f"L{i * step:.1f} {y(b[low]):.1f}"
            for i, b in reversed(list(enumerate(projection.bands)))
        )
        return top + bottom + "Z"

    final = projection.bands[-1]

    def outcome(v: float) -> str:
        return f"{pct(v - 1, 0)} · {pct(v ** (1 / years) - 1)} a year"

    return {
        "mc": {
            "years": f"{years} years",
            "outer": band(0, 4),
            "inner": band(1, 3),
            "median": line_path([b[2] for b in projection.bands], width, height, lo, hi, log=True),
            "samples": [line_path(s, width, height, lo, hi, log=True) for s in projection.samples],
            "median_text": outcome(final[2]),
            "low_text": outcome(final[0]),
            "high_text": outcome(final[4]),
            "loss_text": pct(projection.loss, 0, False),
        },
        "mc_wait": None,
    }


def _scenarios(history: History) -> list[dict]:
    weights = {key: line.weights[-1] for key, line in history.lines.items() if line.weights[-1]}
    details = {key: history.lines[key].details for key in weights}
    out = []
    for case in a.SCENARIOS:
        hit, total = a.scenario(weights, details, case)
        out.append(
            {
                "label": case.label,
                "total": pct(total, 2),
                "cls": tone(total),
                "holdings": ", ".join(sorted(hit, key=lambda k: hit[k])) or DASH,
                "bar": f"{min(100.0, abs(total) / 0.25 * 100):.1f}%",
            }
        )
    return out
