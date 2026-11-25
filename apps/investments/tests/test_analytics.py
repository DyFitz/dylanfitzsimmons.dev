import math
from datetime import date, timedelta

import pytest

from apps.investments import analytics as a

RF = [0.0] * 4


def test_compound_and_growth():
    assert a.compound([0.1, -0.1]) == pytest.approx(-0.01)
    assert a.growth([0.1, -0.5]) == pytest.approx([100, 110, 55])


def test_spread_figures():
    assert a.sd([1, 2, 3, 4]) == pytest.approx(math.sqrt(5 / 3))
    assert a.cov([1, 2, 3], [2, 4, 6]) == pytest.approx(2)
    assert a.beta([2, 4, 6], [1, 2, 3]) == pytest.approx(2)
    assert a.correlation([1, 2, 3], [3, 2, 1]) == pytest.approx(-1)
    assert a.sd([1]) == 0
    assert a.correlation([1, 1], [1, 2]) == 0


def test_quantile_is_linear_between_values():
    assert a.quantile([0, 10], 0.25) == pytest.approx(2.5)
    assert a.quantile([], 0.5) == 0


def test_paired_keeps_days_both_have():
    assert a.paired([1, None, 3], [4, 5, None]) == ([1], [4])


# ---------------------------------------------------------------- periods


def test_periods_count_back_in_trading_days():
    dates = [date(2026, 1, 1) + timedelta(days=i) for i in range(300)]
    assert a.period_start(dates, "1m", 100) == 80
    assert a.period_start(dates, "3m", 100) == 38
    assert a.period_start(dates, "1y", 299) == 47
    assert a.period_start(dates, "all", 299) == 0
    assert a.period_start(dates, "1m", 5) == 0


def test_the_year_to_date_starts_at_the_last_close_of_last_year():
    dates = [date(2025, 12, 30), date(2025, 12, 31), date(2026, 1, 2), date(2026, 1, 5)]
    assert a.period_start(dates, "ytd", 3) == 1


def test_a_period_needs_enough_history():
    assert not a.period_ready("3m", 62)
    assert a.period_ready("3m", 63)
    assert a.period_ready("all", 1)


# ---------------------------------------------------------------- drawdowns and months


def test_drawdowns_find_the_worst_fall_and_its_recovery():
    # 100 → 110 → 88 (down 20% from the peak) → 99 → 121 (back above 110).
    falls = a.drawdowns([0.1, -0.2, 0.125, 2 / 9])
    assert falls.series == pytest.approx([0, -0.2, -0.1, 0])
    assert (falls.worst, falls.worst_at, falls.worst_peak_at) == pytest.approx((-0.2, 1, 0))
    assert falls.recovery_days == 3
    assert falls.current == pytest.approx(0)


def test_a_fall_not_yet_made_back_has_no_recovery():
    falls = a.drawdowns([0.1, -0.2])
    assert falls.recovery_days is None
    assert falls.current == pytest.approx(-0.2)
    assert a.drawdowns([0.01, 0.01]).recovery_days is None


def test_monthly_returns_compound_within_each_month():
    dates = [date(2026, 1, 30), date(2026, 2, 2), date(2026, 2, 3)]
    months = a.monthly(dates, [0.1, 0.1, 0.1])
    assert [(year, month) for year, month, _ in months] == [(2026, 1), (2026, 2)]
    assert [value for _, _, value in months] == pytest.approx([0.1, 0.21])


# ---------------------------------------------------------------- the factsheet


def test_the_factsheet_basics():
    s = a.stats([0.01, -0.02, 0.03, 0.0], RF)
    assert s.days == 4
    assert s.total == pytest.approx(1.01 * 0.98 * 1.03 - 1)
    assert s.cagr is None  # less than a year
    assert s.vol == pytest.approx(a.sd([0.01, -0.02, 0.03, 0.0]) * math.sqrt(252))
    assert (s.best, s.worst, s.hit_rate) == pytest.approx((0.03, -0.02, 0.5))
    assert s.beta is None


def test_sharpe_counts_only_return_above_the_risk_free_rate():
    r = [0.01, -0.01, 0.02, 0.0]
    rf = [0.005] * 4
    expected = (a.mean(r) - 0.005) / a.sd(r) * math.sqrt(252)
    assert a.stats(r, rf).sharpe == pytest.approx(expected)


def test_a_year_of_history_gives_a_yearly_return():
    s = a.stats([0.001] * 252, [0.0] * 252)
    assert s.cagr == pytest.approx(1.001**252 - 1)


def test_against_a_benchmark():
    b = [0.01, -0.02, 0.015, -0.005]
    r = [2 * x for x in b]  # twice the benchmark, every day
    s = a.stats(r, RF, b)
    assert s.beta == pytest.approx(2)
    assert s.correlation == pytest.approx(1)
    assert (s.up_capture, s.down_capture) == pytest.approx((2, 2))
    assert s.alpha == pytest.approx(0)
    assert s.tracking_error == pytest.approx(a.sd(b) * math.sqrt(252))


def test_value_at_risk_and_expected_shortfall():
    r = [x / 100 for x in range(-10, 10)]  # -10% to +9%
    s = a.stats(r, [0.0] * 20)
    assert s.var95 == pytest.approx(-a.quantile(sorted(r), 0.05))
    assert s.cvar95 == pytest.approx(0.10)


def test_rolling_figures_move_along_the_history():
    r = [0.01, -0.01] * 50
    out = a.rolling(r, r, span=20, step=10)
    assert [i for i, _, _ in out] == [20, 30, 40, 50, 60, 70, 80, 90, 100]
    assert all(b == pytest.approx(1) for _, _, b in out)


# ---------------------------------------------------------------- where it came from


def test_contributions_add_up_to_the_return():
    # Two holdings and some costs; day two's points count for more after day one's gain.
    parts = {"A": [0.06, 0.01], "B": [0.04, -0.03]}
    portfolio = [0.1, -0.021]
    totals, total = a.contributions(parts, portfolio)
    assert total == pytest.approx(1.1 * 0.979 - 1)
    assert totals["A"] == pytest.approx(0.06 + 0.01 * 1.1)
    assert totals["other"] == pytest.approx(-0.001 * 1.1)
    assert sum(totals.values()) == pytest.approx(total)


def test_risk_shares_of_holdings_moving_with_the_portfolio():
    portfolio = [0.01, -0.02, 0.03]
    shares = a.risk_shares({"A": 0.5, "B": 0.5}, {"A": portfolio, "B": portfolio}, portfolio)
    assert shares == pytest.approx({"A": 0.5, "B": 0.5})


def test_effective_holdings_and_turnover():
    assert a.effective_holdings([0.25] * 4) == pytest.approx(4)
    assert a.effective_holdings([0.9, 0.1]) == pytest.approx(1 / 0.82)
    assert a.turnover([0.1, -0.1]) == pytest.approx(0.1)


# ---------------------------------------------------------------- benchmarks


def test_the_policy_benchmark_drifts_then_resets_at_the_quarters_end():
    dates = [date(2026, 3, 27), date(2026, 3, 30), date(2026, 3, 31), date(2026, 4, 1)]
    dates.append(date(2026, 4, 2))
    parts = {"shares": [0.10, 0.10, 0.0, 0.10], "cash": [0.0, 0.0, 0.0, 0.0]}
    out = a.policy_returns(dates, parts, {"shares": 0.5, "cash": 0.5})
    assert out[0] == pytest.approx(0.05)
    # After a 10% rise, shares have drifted to 0.55 / 1.05 of it.
    assert out[1] == pytest.approx(0.10 * 0.55 / 1.05)
    # Back to half and half from the close of 31 March.
    assert out[3] == pytest.approx(0.05)


# ---------------------------------------------------------------- what might happen


def test_the_random_numbers_match_the_page_scripts():
    rng = a.Mulberry32(1)
    assert [round(rng.next(), 12) for _ in range(3)] == [
        0.627073940588,
        0.00273572118,
        0.52744703996,
    ]


def test_monte_carlo_is_repeatable_and_ordered():
    r = [0.01, -0.008, 0.004, -0.002] * 40
    one, two = a.monte_carlo(r, 2, seed=3, paths=50), a.monte_carlo(r, 2, seed=3, paths=50)
    assert one == two
    assert len(one.bands) == 25
    assert one.bands[0] == [1, 1, 1, 1, 1]
    assert all(band == sorted(band) for band in one.bands)
    assert 0 <= one.loss <= 1
    assert a.monte_carlo(r, 2, seed=4, paths=50) != one


def test_flat_days_project_nothing():
    projection = a.monte_carlo([0.0] * 50, 1, paths=20)
    assert projection.bands[-1] == pytest.approx([1] * 5)
    assert projection.loss == 0


def test_the_stress_test_splits_market_and_chips():
    market = [0.01, -0.02, 0.015, -0.01, 0.005]
    extra = [0.002, 0.004, -0.003, 0.001, -0.004]  # chips' own moves
    chips = [1.5 * m + e for m, e in zip(market, extra, strict=True)]
    returns = {
        "WORLD": market,
        "CHIP": [m * 1.2 + e * 2 for m, e in zip(market, extra, strict=True)],
        "NEW": [None, None, *market[2:]],
    }
    sens = a.sensitivities(returns, market, chips)
    assert (sens["WORLD"].market, sens["WORLD"].chips) == pytest.approx((1, 0), abs=1e-9)
    assert sens["CHIP"].market == pytest.approx(1.2 + 2 * a.beta(extra, market))
    assert sens["NEW"].market == pytest.approx(1)
    moves, total = a.stress({"WORLD": 0.5, "CHIP": 0.5}, sens, -0.2, 0)
    assert moves["WORLD"] == pytest.approx(-0.2)
    assert total == pytest.approx(0.5 * -0.2 + 0.5 * moves["CHIP"])


def test_the_rationales_scenarios():
    weights = {"MU": 0.04, "SEMI": 0.08, "SGLN": 0.10, "IGLS": 0.05, "BP": 0.04}
    details = {
        "MU": {"symbol": "MU", "sector": "Semiconductors", "sleeve": "growth"},
        "SEMI": {"symbol": "SEMI", "sector": "Semiconductors", "sleeve": "growth"},
        "SGLN": {"symbol": "SGLN", "sector": "Gold", "sleeve": "defence"},
        "IGLS": {"symbol": "IGLS", "sector": "Government bonds", "sleeve": "defence"},
        "BP": {"symbol": "BP", "sector": "Oil and gas", "sleeve": "income"},
    }
    results = {case.label: a.scenario(weights, details, case)[1] for case in a.SCENARIOS}
    assert results == pytest.approx(
        {
            "Chips fall 40%": -0.4 * 0.12,
            "Memory falls 50%": -0.5 * 0.04,
            "Gold falls 20%": -0.2 * 0.10,
            "All shares fall 25%": -0.25 * 0.16,
        }
    )
