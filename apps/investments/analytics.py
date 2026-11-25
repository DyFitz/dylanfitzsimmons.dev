"""The portfolio maths: plain functions over lists of daily returns, with no database.

The formulas match the ones the page's script uses (static/js/modules/invest-maths.js), so the
figures sent with the page and the ones worked out in the browser agree. Returns are daily
fractions, 0.01 being 1%. Yearly figures assume 252 trading days.
"""

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date

TRADING_DAYS = 252

# Trading days of history a figure needs before it means anything.
NEED_PERIOD = {"1m": 20, "3m": 63, "ytd": 1, "1y": 252, "all": 1}
NEED_RATIOS = 63
NEED_ROLLING = 84
NEED_MONTE_CARLO = 126


# ---------------------------------------------------------------- basics


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def sd(xs: Sequence[float]) -> float:
    """The sample standard deviation."""
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def cov(xs: Sequence[float], ys: Sequence[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mx, my = mean(xs), mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / (len(xs) - 1)


def correlation(xs: Sequence[float], ys: Sequence[float]) -> float:
    spread = sd(xs) * sd(ys)
    return cov(xs, ys) / spread if spread else 0.0


def beta(xs: Sequence[float], market: Sequence[float]) -> float:
    spread = sd(market) ** 2
    return cov(xs, market) / spread if spread else 0.0


def compound(xs: Sequence[float]) -> float:
    value = 1.0
    for x in xs:
        value *= 1 + x
    return value - 1


def quantile(ordered: Sequence[float], q: float) -> float:
    """Linear between the two nearest values, as spreadsheets do. `ordered` must be sorted."""
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * q
    lo, hi = math.floor(position), math.ceil(position)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)


def growth(returns: Sequence[float], start: float = 100) -> list[float]:
    """Growth of 100: the value at the start and after each day."""
    values = [start]
    for r in returns:
        values.append(values[-1] * (1 + r))
    return values


def paired(xs: Sequence[float | None], ys: Sequence[float | None]):
    """The days both have a figure for, e.g. a holding and the portfolio."""
    pairs = [(x, y) for x, y in zip(xs, ys, strict=True) if x is not None and y is not None]
    return [x for x, _ in pairs], [y for _, y in pairs]


# ---------------------------------------------------------------- periods


def period_start(dates: Sequence[date], period: str, end: int) -> int:
    """The index of the close a period is measured from, for the period ending at `end`."""
    if period == "1m":
        return max(0, end - 20)
    if period == "3m":
        return max(0, end - 62)
    if period == "1y":
        return max(0, end - 252)
    if period == "ytd":
        i = end
        while i > 0 and dates[i - 1].year == dates[end].year:
            i -= 1
        # The year's return is measured from the last close of the year before.
        return max(0, i - 1)
    return 0


def period_ready(period: str, days: int) -> bool:
    return days >= NEED_PERIOD[period]


# ---------------------------------------------------------------- drawdowns and months


@dataclass(frozen=True)
class Drawdowns:
    series: list[float]
    worst: float
    worst_at: int
    worst_peak_at: int
    recovered_at: int | None
    current: float

    @property
    def recovery_days(self) -> int | None:
        """Trading days from the worst fall's peak until it was made back, if it has been."""
        return None if self.recovered_at is None else self.recovered_at - self.worst_peak_at


def drawdowns(returns: Sequence[float]) -> Drawdowns:
    value = peak = 1.0
    worst = 0.0
    worst_at = peak_at = worst_peak_at = 0
    series = []
    for i, r in enumerate(returns):
        value *= 1 + r
        if value > peak:
            peak, peak_at = value, i
        fall = value / peak - 1
        series.append(fall)
        if fall < worst:
            worst, worst_at, worst_peak_at = fall, i, peak_at
    recovered = next((i for i in range(worst_at, len(series)) if series[i] >= 0), None)
    return Drawdowns(
        series=series,
        worst=worst,
        worst_at=worst_at,
        worst_peak_at=worst_peak_at,
        recovered_at=recovered if worst < 0 else None,
        current=series[-1] if series else 0.0,
    )


def monthly(dates: Sequence[date], returns: Sequence[float]) -> list[tuple[int, int, float]]:
    """(year, month, return) for each calendar month the days fall in."""
    months: list[list] = []
    for day, r in zip(dates, returns, strict=True):
        if not months or (months[-1][0], months[-1][1]) != (day.year, day.month):
            months.append([day.year, day.month, 1.0])
        months[-1][2] *= 1 + r
    return [(year, month, value - 1) for year, month, value in months]


# ---------------------------------------------------------------- the factsheet


@dataclass(frozen=True)
class Stats:
    days: int
    total: float
    cagr: float | None  # only once there is a year of history
    annual: float  # the average day, compounded over a year
    vol: float
    sharpe: float
    sortino: float
    calmar: float
    max_drawdown: float
    current_drawdown: float
    recovery_days: int | None
    var95: float  # a loss, so positive
    cvar95: float
    best: float
    worst: float
    hit_rate: float
    skew: float
    kurtosis: float  # excess
    # Against the benchmark, when there is one.
    bench_total: float | None = None
    beta: float | None = None
    alpha: float | None = None
    correlation: float | None = None
    tracking_error: float | None = None
    information_ratio: float | None = None
    up_capture: float | None = None
    down_capture: float | None = None


def stats(r: Sequence[float], rf: Sequence[float], b: Sequence[float] | None = None) -> Stats:
    """Everything a factsheet shows for a window of daily returns.

    `rf` is the risk-free return for each of the same days, and `b` the benchmark's, if any.
    """
    n = len(r)
    years = n / TRADING_DAYS
    total = compound(r)
    cagr = (1 + total) ** (1 / years) - 1 if years >= 1 else None
    vol = sd(r) * math.sqrt(TRADING_DAYS)
    excess = [x - f for x, f in zip(r, rf, strict=True)]
    sharpe = mean(excess) / sd(r) * math.sqrt(TRADING_DAYS) if sd(r) else 0.0
    downside = math.sqrt(mean([min(0.0, x) ** 2 for x in excess]))
    sortino = mean(excess) / downside * math.sqrt(TRADING_DAYS) if downside else 0.0
    falls = drawdowns(r)
    annual = (1 + mean(r)) ** TRADING_DAYS - 1
    calmar = (cagr if cagr is not None else annual) / abs(falls.worst) if falls.worst else 0.0
    ordered = sorted(r)
    var95 = -quantile(ordered, 0.05)
    tail = [x for x in ordered if x <= -var95]
    m, s = mean(r), sd(r) or 1.0
    figures = {
        "days": n,
        "total": total,
        "cagr": cagr,
        "annual": annual,
        "vol": vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "max_drawdown": falls.worst,
        "current_drawdown": falls.current,
        "recovery_days": falls.recovery_days,
        "var95": var95,
        "cvar95": -mean(tail),
        "best": max(r, default=0.0),
        "worst": min(r, default=0.0),
        "hit_rate": sum(1 for x in r if x > 0) / (n or 1),
        "skew": mean([((x - m) / s) ** 3 for x in r]),
        "kurtosis": mean([((x - m) / s) ** 4 for x in r]) - 3,
    }
    if b is not None:
        bench_beta = beta(r, b)
        rf_mean = mean(rf)
        active = [x - y for x, y in zip(r, b, strict=True)]
        te = sd(active) * math.sqrt(TRADING_DAYS)
        ups = [(x, y) for x, y in zip(r, b, strict=True) if y > 0]
        downs = [(x, y) for x, y in zip(r, b, strict=True) if y < 0]

        def capture(days: list[tuple[float, float]]) -> float:
            theirs = mean([y for _, y in days])
            return mean([x for x, _ in days]) / theirs if theirs else 0.0

        figures |= {
            "bench_total": compound(b),
            "beta": bench_beta,
            "alpha": (m - rf_mean - bench_beta * (mean(b) - rf_mean)) * TRADING_DAYS,
            "correlation": correlation(r, b),
            "tracking_error": te,
            "information_ratio": mean(active) * TRADING_DAYS / te if te else 0.0,
            "up_capture": capture(ups),
            "down_capture": capture(downs),
        }
    return Stats(**figures)


def rolling(
    r: Sequence[float], b: Sequence[float], span: int = 63, step: int = 3
) -> list[tuple[int, float, float]]:
    """(index, volatility, beta) over a moving three-month window, every few days."""
    out = []
    for i in range(span, len(r) + 1, step):
        window, bench = r[i - span : i], b[i - span : i]
        out.append((i, sd(window) * math.sqrt(TRADING_DAYS), beta(window, bench)))
    return out


# ---------------------------------------------------------------- where it came from


def contributions(
    parts: dict[str, Sequence[float]], portfolio: Sequence[float]
) -> tuple[dict[str, float], float]:
    """Each part's points of the return over a window, linked so they add up to the whole.

    `parts` are each holding's (or group's) daily contribution, as fractions of the portfolio.
    A day's points are worth more after the portfolio has grown, so each is scaled by the
    growth up to the day before. Whatever the parts don't explain comes back as "other".
    """
    totals = dict.fromkeys(parts, 0.0)
    value = 1.0
    other = 0.0
    for t, r in enumerate(portfolio):
        explained = 0.0
        for key, series in parts.items():
            totals[key] += series[t] * value
            explained += series[t]
        other += (r - explained) * value
        value *= 1 + r
    totals["other"] = other
    return totals, value - 1


def risk_shares(
    weights: dict[str, float],
    returns: dict[str, Sequence[float | None]],
    portfolio: Sequence[float],
) -> dict[str, float]:
    """Each holding's share of the portfolio's variance: its weight, times its
    covariance with the portfolio, over the portfolio's variance."""
    variance = sd(portfolio) ** 2 or 1.0
    shares = {}
    for key, weight in weights.items():
        mine, theirs = paired(returns[key], portfolio)
        shares[key] = weight * cov(mine, theirs) / variance
    return shares


def effective_holdings(weights: Sequence[float]) -> float:
    """How many equal holdings the portfolio behaves like: one over the sum of squared weights."""
    squares = sum(w * w for w in weights)
    return 1 / squares if squares else 0.0


def turnover(trade_weights: Sequence[float]) -> float:
    """Half of everything bought and sold, as a share of the portfolio."""
    return sum(abs(w) for w in trade_weights) / 2


# ---------------------------------------------------------------- benchmarks


def policy_returns(
    dates: Sequence[date], components: dict[str, Sequence[float]], targets: dict[str, float]
) -> list[float]:
    """A benchmark of fixed target weights, left to drift and reset at each quarter's end.

    `components` are each part's daily returns for the days after the first date.
    """
    weights = dict(targets)
    out = []
    for t in range(1, len(dates)):
        r = sum(weights[k] * components[k][t - 1] for k in weights)
        out.append(r)
        weights = {k: w * (1 + components[k][t - 1]) / (1 + r) for k, w in weights.items()}
        ends_quarter = (
            t + 1 < len(dates) and (dates[t + 1].month - 1) // 3 != (dates[t].month - 1) // 3
        )
        if ends_quarter:
            weights = dict(targets)
    return out


# ---------------------------------------------------------------- what might happen


class Mulberry32:
    """The page script's seeded random numbers, so a seed gives the same futures in both."""

    def __init__(self, seed: int):
        self.a = seed & 0xFFFFFFFF

    def next(self) -> float:
        def imul(x: int, y: int) -> int:
            return (x * y) & 0xFFFFFFFF

        self.a = (self.a + 0x6D2B79F5) & 0xFFFFFFFF
        t = self.a
        t = imul(t ^ (t >> 15), t | 1)
        t ^= (t + imul(t ^ (t >> 7), t | 61)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296


@dataclass(frozen=True)
class Projection:
    bands: list[list[float]]  # 5th, 25th, 50th, 75th and 95th percentiles at each month
    samples: list[list[float]]  # three of the futures, to draw
    loss: float  # the share of futures that end below where they started


def monte_carlo(
    returns: Sequence[float], years: int, seed: int = 1, paths: int = 500, block: int = 10
) -> Projection:
    """Futures built from blocks of real days, so bad weeks come in runs, as they do."""
    rng = Mulberry32(seed)
    steps = round(years * 12)
    per_step = 21
    at_step: list[list[float]] = [[] for _ in range(steps + 1)]
    samples = []
    for p in range(paths):
        value = 1.0
        at_step[0].append(1.0)
        track = [1.0]
        for step in range(1, steps + 1):
            for d in range(0, per_step, block):
                start = math.floor(rng.next() * (len(returns) - block))
                for k in range(min(block, per_step - d)):
                    value *= 1 + returns[start + k]
            at_step[step].append(value)
            track.append(value)
        if p < 3:
            samples.append(track)
    bands = []
    for values in at_step:
        values.sort()
        bands.append([quantile(values, q) for q in (0.05, 0.25, 0.5, 0.75, 0.95)])
    finals = at_step[steps]
    return Projection(bands=bands, samples=samples, loss=sum(v < 1 for v in finals) / len(finals))


@dataclass(frozen=True)
class Sensitivity:
    market: float  # moves with world shares
    chips: float  # and beyond that, with chips


def sensitivities(
    returns: dict[str, Sequence[float | None]], market: Sequence[float], chips: Sequence[float]
) -> dict[str, Sensitivity]:
    """Each holding's beta to the market, then to the part of chips' moves the market doesn't
    explain, so the stress test's two dials don't count the same move twice."""
    chips_beta = beta(chips, market)
    chips_own = [c - chips_beta * m for c, m in zip(chips, market, strict=True)]
    out = {}
    for key, series in returns.items():
        days = [i for i, x in enumerate(series) if x is not None]
        mine = [series[i] for i in days]
        m = [market[i] for i in days]
        to_market = beta(mine, m)
        leftover = [x - to_market * y for x, y in zip(mine, m, strict=True)]
        out[key] = Sensitivity(to_market, beta(leftover, [chips_own[i] for i in days]))
    return out


def stress(
    weights: dict[str, float], sens: dict[str, Sensitivity], market_move: float, chips_move: float
) -> tuple[dict[str, float], float]:
    """Each holding's estimated move for a given market and chip move, and the portfolio's."""
    moves = {
        key: sens[key].market * market_move + sens[key].chips * chips_move
        for key in weights
        if key in sens
    }
    return moves, sum(weights[key] * move for key, move in moves.items())


@dataclass(frozen=True)
class Scenario:
    label: str
    move: float
    picks: Callable[[dict], bool]  # which holdings it hits, given a holding's details


def scenario(
    weights: dict[str, float], details: dict[str, dict], case: Scenario
) -> tuple[dict[str, float], float]:
    """A fall in some holdings with everything else flat, at today's weights."""
    hit = {key: weights[key] * case.move for key in weights if case.picks(details[key])}
    return hit, sum(hit.values())


EQUITY_SLEEVES = {"growth", "income", "defensive"}
SCENARIOS = [
    Scenario("Chips fall 40%", -0.40, lambda h: h["sector"] == "Semiconductors"),
    Scenario("Memory falls 50%", -0.50, lambda h: h["symbol"] in {"MU", "SKHY"}),
    Scenario("Gold falls 20%", -0.20, lambda h: h["sector"] == "Gold"),
    Scenario("All shares fall 25%", -0.25, lambda h: h["sleeve"] in EQUITY_SLEEVES),
]
