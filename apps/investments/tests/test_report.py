import math
from datetime import date, timedelta

import pytest

from apps.investments import report
from apps.investments.flex import parse
from apps.investments.history import History, load
from apps.investments.importer import save
from apps.investments.models import Instrument, Portfolio
from apps.investments.tests.samples import report as sample


@pytest.fixture
def figures(db):
    Portfolio.objects.all().delete()
    Instrument.objects.all().delete()
    portfolio = Portfolio.objects.create(inception=date(2026, 1, 5), cash_target=5)
    save(parse(sample()), source="test.xml")
    Instrument.objects.filter(symbol="AAA").update(sleeve="income", sector="Tobacco")
    Instrument.objects.filter(symbol="BBB").update(sleeve="growth", sector="Semiconductors")
    return report.build(load(), portfolio, date(2026, 1, 9))


def test_formatting():
    assert report.pct(0.0123) == "+1.2%"
    assert report.pct(-0.00001) == "0.0%"
    assert report.pct(None) == report.DASH
    assert report.pct(0.5, 0, signed=False) == "50%"
    assert report.num(1.234) == "1.23"
    assert report.long_date(date(2026, 1, 5)) == "5 Jan 2026"


def test_weekdays_between():
    # Friday 9 Jan to Monday 12 Jan: none in between.
    assert report.weekdays_between(date(2026, 1, 9), date(2026, 1, 12)) == 0
    assert report.weekdays_between(date(2026, 1, 8), date(2026, 1, 14)) == 3


def test_a_young_history_shows_everything_since_the_start(figures):
    assert figures["period_label"] == "All"
    # £1,000 → £1,045, then a £9 gain on £1,145 after £100 was paid in.
    assert figures["tiles"][0]["value"] == "+5.3%"
    assert figures["tiles"][0]["note"] == "in 3 trading days"
    assert figures["tiles"][2]["value"] == report.DASH  # Sharpe waits for three months
    facts = {fact["label"]: fact["value"] for fact in figures["facts"]}
    assert facts["Sortino ratio"] == report.DASH
    assert facts["Best day"] == "+2.80%"


def test_periods_the_history_cant_fill_are_blank(figures):
    [portfolio] = figures["returns"]["rows"]
    assert [cell["text"] for cell in portfolio["cells"]] == [
        report.DASH,
        report.DASH,
        "+5.3%",
        report.DASH,
        "+5.3%",
    ]


def test_the_contributions_add_up(figures):
    points = {row["name"]: row["text"] for row in figures["contributions"]}
    assert points["Cash and costs"] == "+0.00 pts"
    assert figures["contribution_total"] == "+5.32%"


def test_sleeves_against_their_targets(figures):
    sleeves = {row["name"]: row for row in figures["sleeves"]}
    assert sleeves["Cash"]["target"] == "5%"
    assert sleeves["Income and value"]["weight"] == "28.1%"
    assert sleeves["Growth"]["weight"] == "14.3%"


def test_trades_show_the_weight_before_and_after(figures):
    rows = {(t["ticker"], t["date"]): t for t in figures["trades"]}
    assert rows[("AAA", "6 Jan 2026")]["change"] == "0.0% → 50.6%"
    assert rows[("AAA", "6 Jan 2026")]["verb"] == "Bought"
    assert rows[("AAA", "8 Jan 2026")]["verb"] == "Trimmed"
    assert figures["turnover"] == "10% of the portfolio traded in the last year"


def test_the_sector_map_covers_the_whole_box(figures):
    area = sum(float(t["w"][:-1]) * float(t["h"][:-1]) for t in figures["tiles_map"])
    assert area == pytest.approx(100 * 100, rel=1e-3)


def test_long_labels_are_cut_to_fit():
    assert report._fit("Semiconductors", 40) == "Semiconductors"
    assert report._fit("Semiconductors", 15).endswith("…")
    assert report._fit("Semiconductors", 3) == ""


def test_the_scenarios_hit_the_right_holdings(figures):
    cases = {case["label"]: case for case in figures["scenarios"]}
    assert cases["Chips fall 40%"]["holdings"] == "BBB"
    assert cases["All shares fall 25%"]["total"] == "-10.59%"


def _long_history(days: int) -> History:
    dates = [date(2026, 1, 1) + timedelta(days=i) for i in range(days + 1)]
    returns = [0.01 * math.sin(i) for i in range(days)]
    return History(
        dates=dates,
        returns=returns,
        cash=[0.0] * (days + 1),
        lines={},
        risk_free=[0.0] * days,
        risk_free_source="test",
        benchmarks={"policy": [r / 2 for r in returns]},
    )


def test_the_rolling_chart_once_there_are_four_months():
    assert report._rolling(_long_history(83), "policy")["rolling"] is None
    rolling = report._rolling(_long_history(84), "policy")["rolling"]
    assert rolling["beta_now"] == "2.00"
    assert rolling["vol"].startswith("M0.0 ")


def test_the_rolling_chart_needs_the_benchmark():
    wait = report._rolling(_long_history(100), None)["rolling_wait"]
    assert "benchmark's prices" in wait["text"]


def test_monte_carlo_once_there_are_six_months():
    assert report._monte_carlo(_long_history(125))["mc"] is None
    mc = report._monte_carlo(_long_history(126))["mc"]
    assert mc["years"] == "5 years"
    assert len(mc["samples"]) == 3
    assert mc["loss_text"].endswith("%")


def test_the_cumulative_return_axis_is_labelled_in_percent():
    ticks = [report._tick(v) for v in (91.6, 99.7, 100.4, 104.6)]
    assert ticks == ["-8%", "0%", "0%", "+5%"]
