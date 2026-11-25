from datetime import date
from unittest.mock import patch

import pytest
from django.contrib.staticfiles import finders
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains, assertTemplateUsed

from apps.core.navigation import build_navigation
from apps.investments.flex import parse
from apps.investments.importer import save
from apps.investments.models import Instrument, Portfolio, Price, PriceSeries
from apps.investments.tests.samples import report


@pytest.mark.django_db
def test_page_shows_that_it_is_in_progress(client: Client) -> None:
    response = client.get(reverse("investments:page"))

    assert response.status_code == 200
    assertTemplateUsed(response, "investments/investments.html")
    assertContains(response, "<title>Investments \N{EN DASH} ")
    assertContains(response, "In progress")
    assert finders.find("img/investments-in-progress.svg") is not None


def test_investments_link_is_in_the_navigation_and_current_on_its_page() -> None:
    links = build_navigation(reverse("investments:page"))
    investments = next(link for link in links if link.label == "Investments")

    assert investments.url == reverse("investments:page")
    assert investments.aria_current == "page"
    assert [link.label for link in links] == ["Home", "Projects", "CV", "Contact", "Investments"]


# ---------------------------------------------------------------- with a history


@pytest.fixture
def imported(db, settings):
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
    Portfolio.objects.all().delete()
    Instrument.objects.all().delete()
    Portfolio.objects.create(
        inception=date(2026, 1, 5), idea="An **idea**.", holdings="Why.", rules="- A rule"
    )
    save(parse(report()), source="test.xml")


def get(client: Client, today: date):
    with patch("apps.investments.views.timezone.localdate", return_value=today):
        return client.get(reverse("investments:page"))


def test_the_dashboard_replaces_the_notice_once_there_is_history(client: Client, imported) -> None:
    response = get(client, date(2026, 1, 9))

    assertTemplateUsed(response, "investments/dashboard.html")
    assertContains(response, "Up to date: close of 8 Jan 2026.")
    assertContains(response, "Whole history · 5 Jan 2026 to 8 Jan 2026")
    assertContains(response, "<strong>idea</strong>", html=True)
    assertContains(response, "<li>A rule</li>", html=True)
    assertContains(response, "Not enough history yet")
    # Three days of history: the ratios wait, and so does the beta, with no benchmark yet.
    assertContains(response, "once benchmark prices are in")


def test_the_dashboard_has_no_inline_styles_or_scripts(client: Client, imported) -> None:
    html = get(client, date(2026, 1, 9)).content.decode()

    assert " style=" not in html
    assert "<script>" not in html


def test_late_data_is_flagged(client: Client, imported) -> None:
    # The 8 Jan close should have arrived by Monday 12 Jan; by Wednesday it's two days late.
    assertNotContains(get(client, date(2026, 1, 12)), "Out of date")
    response = get(client, date(2026, 1, 14))
    assertContains(response, "iv-status--late")
    assertContains(response, "2 daily updates are missing")


def test_the_display_name_is_used(client: Client, imported) -> None:
    Instrument.objects.filter(symbol="AAA").update(label="Aaa Holdings")
    assertContains(get(client, date(2026, 1, 9)), "Aaa Holdings")


def test_the_page_carries_the_board_and_its_data(client: Client, imported) -> None:
    response = get(client, date(2026, 1, 9))
    html = response.content.decode()

    assert 'id="iv-board-template"' in html
    assert 'id="iv-switch-template"' in html
    # The board's {{placeholders}} reach the browser untouched.
    assert "{{statusText}}" in html
    data = response.context["data"]
    assert data["dates"] == ["2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08"]
    assert {h["ticker"] for h in data["holdings"]} == {"AAA", "BBB"}
    assert data["trades"] == [
        {"day": 1, "ticker": "AAA"},
        {"day": 1, "ticker": "BBB"},
        {"day": 3, "ticker": "AAA"},
    ]


def test_the_data_sent_with_the_page_has_no_amounts_of_money(client: Client, imported) -> None:
    # Every number in it is a date's position, a fraction or a ratio, never above 1 in size,
    # except the day indexes of the trades.
    data = get(client, date(2026, 1, 9)).context["data"]
    numbers = []

    def walk(value, key=""):
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, k)
        elif isinstance(value, list):
            for v in value:
                walk(v, key)
        elif isinstance(value, float | int) and not isinstance(value, bool) and key != "day":
            numbers.append(value)

    walk(data)
    assert numbers
    assert max(abs(x) for x in numbers) <= 1


def test_a_change_in_the_admin_shows_without_waiting_for_the_next_import(
    client: Client, imported, settings
) -> None:
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    assertNotContains(get(client, date(2026, 1, 9)), "Aaa Holdings")
    Instrument.objects.filter(symbol="AAA").update(label="Aaa Holdings")
    assertContains(get(client, date(2026, 1, 9)), "Aaa Holdings")

    before = get(client, date(2026, 1, 9)).content
    series = PriceSeries.objects.create(key="sonia", name="SONIA")
    Price.objects.bulk_create(
        Price(series=series, date=day, close=100 + i / 100)
        for i, day in enumerate([date(2026, 1, 2), date(2026, 1, 6), date(2026, 1, 7)])
    )
    assert get(client, date(2026, 1, 9)).content != before
