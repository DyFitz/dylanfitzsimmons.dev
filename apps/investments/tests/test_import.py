from datetime import date
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from apps.investments.flex import FlexError, parse
from apps.investments.importer import ImportRefusedError, build, save
from apps.investments.models import Day, Holding, ImportRun, Income, Instrument, Portfolio, Trade
from apps.investments.tests.samples import AAA, BBB, START, report


def built(scale: float = 1, start: date = START):
    return build(parse(report(scale)), start)


def by_day(result):
    return {day.date: day for day in result.days}


def holding(result, conid: int, day: date) -> Holding:
    return next(h for c, h in result.holdings if c == conid and h.date == day)


# ---------------------------------------------------------------- reading the report


def test_the_report_is_read():
    statement = parse(report())
    assert statement.values[date(2026, 1, 6)] == 1028
    assert statement.closing == {AAA: 6, BBB: 2}
    assert statement.prices[(BBB, date(2026, 1, 7))] == (110, 0.75)


def test_london_tickers_lose_ibkrs_extra_l():
    assert parse(report()).securities[AAA].symbol == "AAA"


def test_currency_conversions_and_summary_rows_are_left_out():
    statement = parse(report())
    assert [trade.ibkr_id for trade in statement.trades] == ["t1", "t2", "t3"]
    assert [item.ibkr_id for item in statement.cash_items] == ["c1", "c2", "c3"]


def test_something_that_isnt_a_report_is_refused():
    with pytest.raises(FlexError, match="valid XML"):
        parse("not xml")
    with pytest.raises(FlexError, match="Statement generation in progress"):
        parse(
            "<FlexStatementResponse><Status>Warn</Status>"
            "<ErrorMessage>Statement generation in progress</ErrorMessage>"
            "</FlexStatementResponse>"
        )


def test_a_missing_section_is_named():
    xml = report().replace("<Trades>", "<Nothing>").replace("</Trades>", "</Nothing>")
    with pytest.raises(FlexError, match="no Trades section"):
        parse(xml)


# ---------------------------------------------------------------- working out the figures


def test_the_first_day_is_the_starting_point():
    days = by_day(built())
    assert date(2026, 1, 2) not in days
    assert days[START].daily_return == 0
    assert days[START].cash_weight == 1


def test_each_days_return_is_against_the_previous_close():
    days = by_day(built())
    assert days[date(2026, 1, 6)].daily_return == pytest.approx(1028 / 1000 - 1)
    assert days[date(2026, 1, 7)].daily_return == pytest.approx(1045 / 1028 - 1)


def test_money_paid_in_is_not_counted_as_a_gain():
    # £1,045 became £1,154 with £100 paid in: the gain is £9 on £1,145.
    days = by_day(built())
    assert days[date(2026, 1, 8)].daily_return == pytest.approx(9 / 1145)
    assert days[date(2026, 1, 8)].flow == pytest.approx(100 / 1045)


def test_a_holding_bought_today_is_valued_at_the_close():
    result = built()
    assert holding(result, AAA, date(2026, 1, 6)).weight == pytest.approx(520 / 1028)
    assert holding(result, AAA, date(2026, 1, 6)).contribution == pytest.approx(20 / 1000)


def test_returns_are_in_pounds_including_the_currency():
    # BBB rose from $105 to $110 but the dollar fell from £0.80 to £0.75: £168 became £165.
    result = built()
    assert holding(result, BBB, date(2026, 1, 7)).contribution == pytest.approx(-3 / 1028)


def test_a_sale_counts_what_it_made_against_the_close():
    # Sold 4 at £55 with the close at £54: £4 better than holding them at the close.
    result = built()
    assert holding(result, AAA, date(2026, 1, 8)).contribution == pytest.approx(4 / 1145)
    assert holding(result, AAA, date(2026, 1, 8)).weight == pytest.approx(324 / 1154)


def test_holdings_income_and_costs_add_up_to_the_days_return():
    result = built()
    for day in result.days[1:]:
        held = sum(h.contribution for _, h in result.holdings if h.date == day.date)
        income = sum(i.weight for _, i in result.income if i.date == day.date)
        assert held + income == pytest.approx(day.daily_return)


def test_weights_and_cash_add_up_to_the_whole():
    result = built()
    for day in result.days:
        held = sum(h.weight for _, h in result.holdings if h.date == day.date)
        assert held + day.cash_weight == pytest.approx(1)


def test_trades_and_dividends_are_sized_against_the_portfolio():
    result = built()
    trades = {trade.ibkr_id: trade for _, trade in result.trades}
    assert trades["t1"].weight == pytest.approx(500 / 1000)
    assert trades["t2"].weight == pytest.approx(160 / 1000)
    assert trades["t3"].side == Trade.Side.SELL
    [(conid, dividend)] = result.income
    assert conid == AAA
    assert dividend.weight == pytest.approx(5 / 1145)


def test_days_before_the_record_starts_are_left_out():
    result = built(start=date(2026, 1, 7))
    assert [day.date for day in result.days] == [date(2026, 1, 7), date(2026, 1, 8)]
    assert result.days[0].daily_return == 0
    assert {trade.ibkr_id for _, trade in result.trades} == {"t3"}


def test_income_from_before_the_record_starts_is_left_out():
    # The same dividend, paid on 6 Jan instead, with the record starting on 8 Jan.
    xml = report().replace(
        'dateTime="20260108;120000" amount="5', 'dateTime="20260106;120000" amount="5'
    )
    assert built(start=date(2026, 1, 8)).income
    assert build(parse(xml), date(2026, 1, 8)).income == []


def test_a_report_ending_before_the_record_starts_is_refused():
    with pytest.raises(ImportRefusedError):
        built(start=date(2026, 2, 1))


def test_nothing_kept_is_an_amount_of_money():
    # A portfolio a thousand times the size gives exactly the same figures.
    small, large = built(), built(scale=1000)
    for a, b in zip(small.days, large.days, strict=True):
        assert (a.daily_return, a.cash_weight) == pytest.approx((b.daily_return, b.cash_weight))
    for (_, a), (_, b) in zip(small.holdings, large.holdings, strict=True):
        assert (a.weight, a.contribution, a.price) == pytest.approx(
            (b.weight, b.contribution, b.price)
        )
    for (_, a), (_, b) in zip(small.trades, large.trades, strict=True):
        assert a.weight == pytest.approx(b.weight)


# ---------------------------------------------------------------- saving


def test_an_import_saves_everything(portfolio):
    run = save(parse(report()), source="test.xml")
    assert (run.status, run.days, run.period_to) == ("ok", 4, date(2026, 1, 8))
    assert Day.objects.count() == 4
    assert Holding.objects.filter(date=date(2026, 1, 8)).count() == 2
    assert Trade.objects.count() == 3
    assert Income.objects.get().instrument.symbol == "AAA"


def test_importing_again_replaces_rather_than_repeats(portfolio):
    save(parse(report()), source="test.xml")
    save(parse(report()), source="test.xml")
    assert Day.objects.count() == 4
    assert Holding.objects.count() == 2 + 2 + 2
    assert Trade.objects.count() == 3


def test_an_import_keeps_what_was_set_in_the_admin(portfolio):
    Instrument.objects.create(
        conid=AAA, symbol="OLD", name="Old", currency="GBP", sector="Tobacco", sleeve="income"
    )
    save(parse(report()), source="test.xml")
    aaa = Instrument.objects.get(conid=AAA)
    assert (aaa.symbol, aaa.name) == ("AAA", "AAA PLC")
    assert (aaa.sector, aaa.sleeve) == ("Tobacco", "income")
    assert Instrument.objects.get(conid=BBB).region == "US"


def test_an_import_needs_the_portfolio_set_up(db):
    Portfolio.objects.all().delete()
    with pytest.raises(ImportRefusedError, match="admin"):
        save(parse(report()), source="test.xml")


# ---------------------------------------------------------------- the command


def test_the_command_imports_a_file(portfolio, tmp_path):
    path = tmp_path / "report.xml"
    path.write_text(report())
    out = StringIO()
    call_command("import_flex", str(path), stdout=out)
    assert out.getvalue().strip() == "Imported 4 days, 05 Jan 2026 to 08 Jan 2026."


def test_the_command_records_a_failure(portfolio, tmp_path):
    path = tmp_path / "report.xml"
    path.write_text("<broken")
    with pytest.raises(CommandError, match="valid XML"):
        call_command("import_flex", str(path))
    run = ImportRun.objects.get()
    assert (run.status, run.source) == ("failed", "report.xml")


# ---------------------------------------------------------------- the plan


@pytest.mark.django_db
def test_the_plans_targets_add_up_to_the_whole():
    portfolio = Portfolio.load()
    targets = sum(i.target_weight for i in Instrument.objects.all())
    assert portfolio.inception == date(2026, 10, 15)
    assert targets + portfolio.cash_target == 100
    assert not Instrument.objects.filter(sleeve="").exists()
