import pytest
from django.template import Context
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import assertContains

from apps.core.navigation import NavLink, aria_current, build_navigation
from apps.core.templatetags.navigation import main_nav


@pytest.mark.parametrize(
    ("link_url", "current_path", "expected"),
    [
        ("/", "/", "page"),
        ("/", "/projects/", None),
        ("/projects/", "/projects/", "page"),
        ("/projects/", "/projects/this-site/", "true"),
        ("/projects/", "/", None),
        ("/projects/", "/projects-archive/", None),
    ],
)
def test_aria_current(link_url: str, current_path: str, expected: str | None) -> None:
    assert aria_current(link_url, current_path) == expected


def test_build_navigation_marks_the_current_page() -> None:
    home = build_navigation(reverse("core:home"))[0]

    assert home.label == "Home"
    assert home.aria_current == "page"


def test_cv_link_goes_to_the_cv_page_and_is_current_there(client: Client) -> None:
    cv = next(link for link in build_navigation(reverse("cv:page")) if link.label == "CV")

    assert cv.url == reverse("cv:page")
    assert cv.aria_current == "page"


def test_contact_link_goes_to_the_contact_page_and_is_current_after_sending() -> None:
    def contact(path: str) -> NavLink:
        return next(link for link in build_navigation(path) if link.label == "Contact")

    assert contact(reverse("contact:page")).url == reverse("contact:page")
    assert contact(reverse("contact:page")).aria_current == "page"
    assert contact(reverse("contact:sent")).aria_current == "true"


def test_every_link_goes_to_a_page_of_its_own() -> None:
    assert all("#" not in link.url for link in build_navigation("/"))


def test_rendered_navigation_marks_exactly_one_current_page(client: Client) -> None:
    response = client.get(reverse("core:home"))

    assertContains(response, 'aria-current="page"', count=1)


def test_navigation_tag_works_without_a_request() -> None:
    # Email templates, for example, are rendered without a request.
    links = main_nav(Context({}))["links"]

    assert all(link.aria_current is None for link in links)
