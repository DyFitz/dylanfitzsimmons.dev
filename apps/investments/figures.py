"""The portfolio's figures, built once per change and shared by the investments page and the
banner on the home page."""

from django.core.cache import cache
from django.db.models import Count, Max
from django.utils import timezone

from apps.investments import report
from apps.investments.history import load
from apps.investments.models import Day, ImportRun, Instrument, Portfolio, Price

# The banner's bar of sleeves is drawn on a 1000-unit width, with a small gap between them.
BAR_WIDTH = 1000
BAR_GAP = 4
# Shorter names where the full one won't fit a fifth of the banner.
SHORT_NAMES = {"Defensive equities": "Defensive"}


def figures(portfolio: Portfolio | None) -> dict | None:
    """The page's figures, or None until there's a portfolio with any history."""
    latest = Day.objects.order_by("-date").values_list("date", flat=True).first()
    if portfolio is None or latest is None:
        return None
    today = timezone.localdate()
    run = ImportRun.objects.order_by("-pk").values_list("pk", flat=True).first()
    # The figures change with an import, with the day (the status line), with what's set in the
    # admin for each holding, and with prices added by hand.
    plan = hash(
        tuple(
            Instrument.objects.values_list(
                "pk", "label", "sleeve", "sector", "region", "target_weight", "benchmark_only"
            )
        )
    )
    prices = Price.objects.aggregate(count=Count("pk"), last=Max("pk"))
    key = (
        f"investments:{latest}:{run}:{today}:{plan}:{portfolio.cash_target}:"
        f"{prices['count']}:{prices['last']}"
    )
    built = cache.get(key)
    if built is None:
        history = load()
        built = report.build(history, portfolio, today) if history else None
        cache.set(key, built, 60 * 60 * 24)
    return built


def banner() -> dict | None:
    """What the home page shows of the portfolio: how it's split across its sleeves, and its
    growth against the benchmarks, with each holding's latest move for the tape. None until
    there's any history."""
    built = figures(Portfolio.load())
    if built is None:
        return None
    sleeves, x = [], 0.0
    for i, sleeve in enumerate(built["sleeves"]):
        width = float(sleeve["weight"].rstrip("%")) / 100 * BAR_WIDTH
        sleeves.append(
            {
                **sleeve,
                "name": SHORT_NAMES.get(sleeve["name"], sleeve["name"]),
                "step": i,
                "x": f"{x:.1f}",
                "width": f"{max(width - BAR_GAP, 0.0):.1f}",
            }
        )
        x += width
    holdings = next(tile["value"] for tile in built["tiles"] if tile["label"] == "Holdings")
    return {
        "inception": built["inception"],
        "as_of": built["as_of"],
        "days": built["days"],
        "holdings": holdings,
        "sleeves_held": sum(1 for sleeve in sleeves if sleeve["name"] != "Cash"),
        "period_label": built["period_label"],
        "sleeves": sleeves,
        "asset_mix": built["asset_mix"],
        "lines": built["growth_lines"],
        "area": built["growth_area"],
        "tape": [
            {
                "ticker": row["ticker"],
                "weight": row["weight"],
                "day": row["cells"][0]["text"],
                "cls": row["cells"][0]["cls"],
            }
            for row in built["holdings"]
        ],
    }
