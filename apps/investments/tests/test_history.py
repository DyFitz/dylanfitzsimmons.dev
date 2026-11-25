from datetime import date

import pytest
from django.test import override_settings

from apps.investments import analytics
from apps.investments.flex import parse
from apps.investments.history import POLICY, chips, load
from apps.investments.importer import save
from apps.investments.models import Instrument, Portfolio, Price, PriceSeries
from apps.investments.tests.samples import report

DATES = [date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 7), date(2026, 1, 8)]


@pytest.fixture
def history(db):
    Portfolio.objects.all().delete()
    Instrument.objects.all().delete()
    Portfolio.objects.create(inception=DATES[0])
    save(parse(report()), source="test.xml")
    return load()


def test_nothing_to_load_yet(db):
    Portfolio.objects.all().delete()
    assert load() is None


def test_the_series_line_up(history):
    assert history.dates == DATES
    assert history.days == 3
    assert history.returns == pytest.approx([1028 / 1000 - 1, 1045 / 1028 - 1, 9 / 1145])
    assert history.cash[0] == 1


def test_a_holdings_return_is_in_pounds_with_its_dividends(history):
    bbb, aaa = history.lines["BBB"], history.lines["AAA"]
    # Not held going into the first day; then $105 → $110 with $1 going from £0.80 to £0.75.
    assert bbb.returns[0] is None
    assert bbb.returns[1] == pytest.approx(110 * 0.75 / (105 * 0.8) - 1)
    # Flat on 8 Jan, but paid £5 on £540.
    assert aaa.returns[2] == pytest.approx(5 / 540)


def test_contributions_include_dividends_and_add_up(history):
    parts = {key: line.contributions for key, line in history.lines.items()}
    totals, total = analytics.contributions(parts, history.returns)
    assert total == pytest.approx(analytics.compound(history.returns))
    assert totals["AAA"] == pytest.approx(
        0.02 + (20 / 1028) * 1.028 + (4 / 1145 + 5 / 1145) * 1.045
    )
    assert totals["other"] == pytest.approx(0, abs=1e-12)


def test_without_sonia_a_set_rate_stands_in(history):
    assert history.risk_free_source == "4.0% a year"
    assert history.risk_free[0] == pytest.approx(1.04 ** (1 / 252) - 1)


@override_settings(INVESTMENTS_RISK_FREE=0.05)
def test_the_stand_in_rate_is_a_setting(history):
    assert load().risk_free_source == "5.0% a year"


def _prices(key: str, closes: dict[date, float]) -> None:
    series = PriceSeries.objects.create(key=key, name=key)
    Price.objects.bulk_create(Price(series=series, date=d, close=c) for d, c in closes.items())


def test_sonia_is_the_risk_free_rate_once_loaded(history):
    # Not yet published for 8 Jan: that day earns the latest day's rate until it is.
    _prices("sonia", {date(2026, 1, 2): 100, date(2026, 1, 6): 100.02, date(2026, 1, 7): 100.03})
    loaded = load()
    assert loaded.risk_free_source == "SONIA"
    latest = 100.03 / 100.02 - 1
    assert loaded.risk_free == pytest.approx([0.0002, latest, latest])


def test_sonia_accrues_over_a_weekend_at_its_daily_rate(history):
    # Published up to 2 Jan, two days after the figure before: each later day earns half that.
    _prices("sonia", {date(2025, 12, 31): 100, date(2026, 1, 2): 100.02})
    loaded = load()
    daily = (100.02 / 100) ** 0.5
    assert loaded.risk_free == pytest.approx([daily - 1] * 3)


def test_a_benchmark_with_a_missing_part_is_left_out(history):
    assert history.benchmarks == {}
    _prices("acwi", {date(2026, 1, 5): 10, date(2026, 1, 6): 11, date(2026, 1, 8): 11})
    loaded = load()
    assert loaded.benchmarks["acwi"] == pytest.approx([0.1, 0, 0])
    assert "policy" not in loaded.benchmarks


def test_a_series_starting_after_the_record_is_left_out(history):
    _prices("acwi", {date(2026, 1, 6): 11})
    assert load().benchmarks == {}


def test_the_policy_benchmark_once_every_part_is_there(history, monkeypatch):
    # AAA stands in for a held fund, which the made-up account doesn't have.
    monkeypatch.setattr("apps.investments.history.POLICY", {"acwi": 0.75, "aaa": 0.25})
    monkeypatch.setattr("apps.investments.history.HELD", {"aaa": "AAA"})
    _prices("acwi", dict(zip(DATES, [10, 11, 11, 11], strict=True)))
    # AAA wasn't held going into the first day, and there's no series to fill it in.
    assert "policy" not in load().benchmarks
    _prices("aaa", {DATES[0]: 50, DATES[1]: 60})
    policy = load().benchmarks["policy"]
    # The first day from the series (+20%), then AAA's own returns from IBKR.
    assert policy[0] == pytest.approx(0.75 * 0.1 + 0.25 * 0.2)
    # AAA has drifted up to 0.25 * 1.2 / 1.125 of it, and IBKR has it at £52 → £54.
    assert policy[1] == pytest.approx(0.25 * 1.2 / 1.125 * (54 / 52 - 1))


def test_the_policy_is_the_rationales():
    assert POLICY == {"acwi": 0.75, "igls": 0.05, "erns": 0.05, "sgln": 0.10, "sonia": 0.05}


def test_chips_against_the_chip_fund(history, monkeypatch):
    assert chips(history) is None  # there's no chip fund in the made-up account
    # With AAA as the chip fund and BBB as the chip holding, from 7 Jan, when both were held.
    monkeypatch.setattr("apps.investments.history.CHIPS_FUND", "AAA")
    Instrument.objects.filter(symbol="BBB").update(sector="Semiconductors")
    start, sleeve, fund = chips(load())
    assert start == 1
    assert sleeve == pytest.approx([(-3 / 1028) / (168 / 1028), 0])
    assert fund[0] == pytest.approx(54 / 52 - 1)
