from django.contrib.staticfiles import finders
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import assertContains, assertTemplateUsed

from apps.core.navigation import build_navigation


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
