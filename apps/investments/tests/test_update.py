from datetime import date
from io import BytesIO, StringIO

import pytest
from django.conf import settings as django_settings
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import CommandError, call_command

from apps.investments import history, sources, update
from apps.investments.flex import parse
from apps.investments.importer import save
from apps.investments.models import ImportRun, Instrument, Price, PriceSeries, Trade
from apps.investments.tests.samples import AAA, report

SENT = """<FlexStatementResponse timestamp="x"><Status>Success</Status>
<ReferenceCode>123</ReferenceCode><Url>https://example.test/GetStatement</Url>
</FlexStatementResponse>"""
WAIT = """<FlexStatementResponse><Status>Warn</Status><ErrorCode>1019</ErrorCode>
<ErrorMessage>Statement generation in progress.</ErrorMessage></FlexStatementResponse>"""
REFUSED = """<FlexStatementResponse><Status>Fail</Status><ErrorCode>1012</ErrorCode>
<ErrorMessage>Token has expired.</ErrorMessage></FlexStatementResponse>"""
SONIA = """DATE,IUDZOS2
05 Jan 2026,1100.0000
06 Jan 2026,1100.1200
07 Jan 2026,1100.2400
"""


class Reply(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def server(*bodies: str | Exception):
    """A stand-in for urlopen that answers with each body in turn and records the requests."""
    answers = list(bodies)
    seen = []

    def opener(request, timeout):
        seen.append(request)
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return Reply(answer.encode())

    opener.seen = seen
    return opener


@pytest.fixture
def flex(settings):
    settings.IBKR_FLEX_TOKEN = "token"
    settings.IBKR_FLEX_QUERY_ID = "42"
    settings.IBKR_FLEX_TOKEN_EXPIRES = ""
    return settings


# ---------------------------------------------------------------- IBKR


def test_the_report_is_asked_for_then_collected():
    opener = server(SENT, WAIT, "<FlexQueryResponse/>")
    naps = []
    data = sources.fetch_flex_report("token", "42", opener=opener, sleep=naps.append, wait=5)
    assert data == b"<FlexQueryResponse/>"
    assert naps == [5]
    first, last = opener.seen[0], opener.seen[-1]
    assert "SendRequest?t=token&q=42&v=3" in first.full_url
    assert last.full_url == "https://example.test/GetStatement?t=token&q=123&v=3"
    assert first.get_header("User-agent") == sources.USER_AGENT


def test_a_refusal_is_reported_with_ibkrs_reason():
    with pytest.raises(sources.SourceError, match=r"1012.*Token has expired"):
        sources.fetch_flex_report("token", "42", opener=server(REFUSED))


def test_a_refusal_when_collecting_is_reported():
    with pytest.raises(sources.SourceError, match="1012"):
        sources.fetch_flex_report("token", "42", opener=server(SENT, REFUSED))


def test_waiting_gives_up_eventually():
    opener = server(SENT, WAIT, WAIT, WAIT)
    with pytest.raises(sources.SourceError, match="3 tries"):
        sources.fetch_flex_report("t", "q", opener=opener, sleep=lambda _: None, tries=3)


def test_the_token_and_query_are_needed():
    with pytest.raises(sources.SourceError, match="IBKR_FLEX_TOKEN"):
        sources.fetch_flex_report("", "42")


def test_a_refused_request_shows_what_came_back():
    from urllib.error import HTTPError

    refused = HTTPError("https://x.test", 403, "Forbidden", {}, BytesIO(b"<h1>Access Denied</h1>"))
    with pytest.raises(sources.SourceError, match=r"403.*\(Access Denied\)"):
        sources.fetch_flex_report("t", "q", opener=server(refused))


def test_a_network_failure_is_a_source_error():
    with pytest.raises(sources.SourceError, match="Couldn't reach"):
        sources.fetch_flex_report("t", "q", opener=server(OSError("down")))


def test_a_reply_that_isnt_xml_is_a_source_error():
    with pytest.raises(sources.SourceError, match="isn't XML"):
        sources.fetch_flex_report("t", "q", opener=server("<html"))


# ---------------------------------------------------------------- SONIA and price files


def test_sonia_is_read_from_the_bank_of_england():
    opener = server(SONIA)
    rows = sources.fetch_sonia(date(2026, 1, 2), opener=opener)
    assert rows[0] == (date(2026, 1, 5), 1100.0)
    assert len(rows) == 3
    assert "Datefrom=02%2FJan%2F2026" in opener.seen[0].full_url
    assert "SeriesCodes=IUDZOS2" in opener.seen[0].full_url


def test_an_empty_sonia_reply_is_an_error():
    with pytest.raises(sources.SourceError, match=r"no SONIA.*Please try later"):
        sources.fetch_sonia(date(2026, 1, 2), opener=server("<p>Please try later</p>"))


@pytest.mark.parametrize(
    ("text", "first"),
    [
        ("Date,Open,High,Low,Close,Adj Close,Volume\n2026-01-05,1,2,0.5,7.5,7.4,100\n", 7.4),
        ('Date,Price,Open\n"Jan 05, 2026","7,512.0",7400\n', 7512.0),
        ("Date;x\n", None),
        ("Date\tOpen\tClose\tAdj Close\n5 Jan 2026\t7,400.00\t7,512.00\t7,512.00\n", 7512.0),
        ("Date,Close\n05-Jan-26,7512\n", 7512.0),
        (
            'Date,Open,Close*,Adj Close**,Volume\n"5 Jan 2026","7,400","7,512","7,512",9\n',
            7512.0,
        ),
        ("date,close\n05/01/2026,£7.50\nnot a date,1\n06/01/2026,\n", 7.5),
    ],
)
def test_price_files_in_the_usual_layouts_are_read(text, first):
    rows = sources.read_prices(text)
    assert (rows[0][1] if rows else None) == first
    if rows:
        assert rows[0][0] == date(2026, 1, 5)


def test_pence_are_spotted_and_converted():
    known = {date(2026, 1, 6): 75.0}
    rows, factor = sources.match_units(
        [(date(2026, 1, 5), 7400.0), (date(2026, 1, 6), 7510.0)], known
    )
    assert factor == 0.01
    assert rows[0] == (date(2026, 1, 5), 74.0)


def test_matching_units_are_left_alone():
    rows = [(date(2026, 1, 6), 75.2)]
    assert sources.match_units(rows, {date(2026, 1, 6): 75.0}) == (rows, 1.0)
    assert sources.match_units(rows, {}) == (rows, 1.0)


# ---------------------------------------------------------------- funds held as benchmarks


def test_a_benchmark_fund_is_marked_and_its_prices_kept(portfolio):
    save(parse(report().replace("AAAl", "SSACl")), source="test.xml")
    fund = Instrument.objects.get(conid=AAA)
    assert (fund.symbol, fund.benchmark_only, fund.series_key) == ("SSAC", True, "acwi")
    prices = dict(Price.objects.filter(series__key="acwi").values_list("date", "close"))
    assert prices[date(2026, 1, 7)] == 54
    assert PriceSeries.objects.get(key="acwi").source == "IBKR"


def test_a_benchmark_fund_stays_off_the_page(portfolio):
    save(parse(report().replace("AAAl", "SSACl")), source="test.xml")
    loaded = history.load()
    assert "SSAC" not in loaded.lines
    assert "BBB" in loaded.lines
    assert all(trade.instrument.symbol != "SSAC" for trade in loaded.trades)
    assert Trade.objects.filter(instrument__symbol="SSAC").exists()


# ---------------------------------------------------------------- the daily update


def test_the_update_imports_the_account_and_sonia(portfolio, flex):
    opener = server(SENT, report(), SONIA)
    outcome = update.run(date(2026, 1, 9), opener=opener, sleep=lambda _: None)
    assert outcome.failed == []
    assert outcome.done[0] == "Account: 4 days, 05 Jan to 08 Jan 2026."
    assert Price.objects.filter(series__key="sonia").count() == 3
    assert {run.source for run in ImportRun.objects.all()} == {
        update.FLEX_SOURCE,
        update.SONIA_SOURCE,
    }
    assert "Datefrom=29%2FDec%2F2025" in opener.seen[-1].full_url


def test_sonia_is_collected_from_a_week_before_the_last_kept(portfolio, flex):
    update.store_prices("sonia", [(date(2026, 1, 20), 1101.0)], source="x", scale=1)
    opener = server(SONIA)
    update.update_sonia(update.Outcome(), opener=opener)
    assert "Datefrom=13%2FJan%2F2026" in opener.seen[0].full_url


def test_one_source_failing_doesnt_stop_the_other(portfolio, flex):
    outcome = update.run(date(2026, 1, 9), opener=server(REFUSED, SONIA))
    assert outcome.failed == [
        f"{update.FLEX_SOURCE}: IBKR refused the request (1012): Token has expired."
    ]
    assert outcome.done == ["SONIA: up to 07 Jan 2026."]
    failed = ImportRun.objects.get(status="failed")
    assert failed.source == update.FLEX_SOURCE


def test_a_failure_is_emailed_and_the_command_fails(portfolio, flex, monkeypatch):
    with pytest.raises(CommandError, match="Token has expired"):
        _command(monkeypatch, server(REFUSED, OSError("down")))
    message = mail.outbox[0]
    assert message.subject == "[dylanfitzsimmons.dev] Portfolio update failed"
    assert "Token has expired" in message.body
    assert "Couldn't reach" in message.body
    assert message.to == [flex.CONTACT_EMAIL]


def test_a_good_day_sends_nothing(portfolio, flex, monkeypatch):
    out = _command(monkeypatch, server(SENT, report(), SONIA))
    assert "Account: 4 days" in out
    assert mail.outbox == []


def _command(monkeypatch, opener) -> str:
    """Runs the command with the network swapped for `opener`."""
    original = update.run
    monkeypatch.setattr(
        update, "run", lambda today: original(today, opener=opener, sleep=lambda _: None)
    )
    out = StringIO()
    call_command("update_investments", stdout=out, stderr=StringIO())
    return out.getvalue()


@pytest.mark.parametrize(
    ("expires", "today", "warned"),
    [
        ("2027-10-27", date(2027, 9, 27), True),
        ("2027-10-27", date(2027, 9, 28), False),
        ("2027-10-27", date(2027, 10, 27), True),
        ("2027-10-27", date(2027, 11, 2), True),
        ("2027-10-27", date(2026, 11, 25), False),
        ("", date(2027, 10, 27), False),
        ("soon", date(2027, 10, 27), True),
    ],
)
def test_the_token_reminder(settings, expires, today, warned):
    settings.IBKR_FLEX_TOKEN_EXPIRES = expires
    outcome = update.Outcome()
    update.check_token(outcome, today)
    assert bool(outcome.warnings) is warned


def test_a_reminder_alone_is_emailed_as_a_reminder(settings):
    update.report(update.Outcome(done=["SONIA: fine."], warnings=["Token expires."]))
    assert mail.outbox[0].subject.endswith("Portfolio update: a reminder")
    assert mail.outbox[0].body == "Token expires.\n\nSONIA: fine."


# ---------------------------------------------------------------- loading prices by hand


def test_the_price_command_converts_pence(db, tmp_path):
    update.store_prices("acwi", [(date(2026, 1, 6), 75.0)], source="IBKR", scale=1)
    path = tmp_path / "ssac.csv"
    path.write_text("Date,Close\n2026-01-05,7400\n2026-01-06,7500\n")
    out = StringIO()
    call_command("import_prices", "acwi", str(path), stdout=out)
    assert "converted from pence" in out.getvalue()
    assert Price.objects.get(series__key="acwi", date=date(2026, 1, 5)).close == 74.0


def test_the_price_command_warns_when_units_cant_be_checked(db, tmp_path):
    path = tmp_path / "igls.csv"
    path.write_text("Date,Close\n2026-01-05,1300\n")
    err = StringIO()
    call_command("import_prices", "igls", str(path), "--pence", stdout=StringIO(), stderr=err)
    assert err.getvalue() == ""
    assert Price.objects.get(series__key="igls").close == 13.0
    call_command("import_prices", "erns", str(path), stdout=StringIO(), stderr=err)
    assert "can't be checked" in err.getvalue()


def test_pence_are_spotted_from_a_held_funds_closes(portfolio, tmp_path):
    save(parse(report()), source="test.xml")
    Instrument.objects.filter(conid=AAA).update(series_key="aaa")
    path = tmp_path / "aaa.csv"
    path.write_text("Date,Close\n2026-01-06,5200\n2026-01-07,5400\n")
    err = StringIO()
    call_command("import_prices", "aaa", str(path), stdout=StringIO(), stderr=err)
    assert err.getvalue() == ""
    assert Price.objects.get(series__key="aaa", date=date(2026, 1, 6)).close == 52


def test_the_price_command_refuses_an_empty_file(db, tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("nothing here\n")
    with pytest.raises(CommandError, match="No dates"):
        call_command("import_prices", "acwi", str(path))


def test_prices_can_be_uploaded_in_the_admin(admin_client):
    series = PriceSeries.objects.create(key="acwi", name="World shares")
    upload = SimpleUploadedFile("ssac.csv", b"Date,Close\n2026-01-05,7400\n", "text/csv")
    url = f"/{_admin_url()}investments/priceseries/{series.pk}/change/"
    form = admin_client.get(url).context["adminform"].form
    response = admin_client.post(
        url,
        {
            **{name: form.initial.get(name, "") for name in ("key", "name", "currency", "source")},
            "prices": upload,
            "units": "pence",
            "prices-TOTAL_FORMS": "0",
            "prices-INITIAL_FORMS": "0",
        },
        follow=True,
    )
    assert "Added 1 prices" in response.content.decode()
    assert Price.objects.get(series=series).close == 74.0


def test_an_upload_that_isnt_prices_is_refused(admin_client):
    series = PriceSeries.objects.create(key="acwi", name="World shares")
    url = f"/{_admin_url()}investments/priceseries/{series.pk}/change/"
    response = admin_client.post(
        url,
        {
            "key": "acwi",
            "name": "World shares",
            "currency": "GBP",
            "prices": SimpleUploadedFile("x.csv", b"\xff\xfe\x00junk", "text/csv"),
            "prices-TOTAL_FORMS": "0",
            "prices-INITIAL_FORMS": "0",
        },
    )
    assert response.status_code == 200
    assert "text CSV" in response.content.decode() or "No dates" in response.content.decode()


def _admin_url() -> str:
    return django_settings.ADMIN_URL
