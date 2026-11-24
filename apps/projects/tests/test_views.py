import json

import pytest
from django.contrib.staticfiles import finders
from django.test import Client
from django.urls import reverse
from pytest_django import Settings
from pytest_django.asserts import assertContains, assertNotContains

from apps.projects.models import Project

pytestmark = pytest.mark.django_db


def test_list_shows_the_published_projects(client: Client) -> None:
    Project.objects.create(
        title="Hidden one", slug="hidden-one", summary="s", stack="Python", is_published=False
    )

    response = client.get(reverse("projects:list"))

    # The three projects the second migration adds.
    assertContains(response, "Opus Equi")
    assertContains(response, "Enular")
    assertNotContains(response, "Hidden one")


def test_list_gives_the_script_its_data(client: Client) -> None:
    response = client.get(reverse("projects:list"))

    data = response.context["desk_data"]
    assert [project["slug"] for project in data["projects"]] == ["this-site", "opus-equi", "enular"]
    assert data["projects"][0]["code"] == "WIP"
    assert data["projects"][0]["href"] == reverse("projects:detail", kwargs={"slug": "this-site"})
    # It has to survive the trip into the page as JSON.
    assert json.loads(json.dumps(data)) == data
    assertContains(response, 'id="projects-data"')


def test_list_gives_the_script_its_links_and_photographs(
    client: Client, settings: Settings
) -> None:
    response = client.get(reverse("projects:list"))

    data = response.context["desk_data"]
    home = reverse("core:home")
    assert data["urls"] == {
        "home": home,
        "cv": reverse("cv:page"),
        "contact": reverse("contact:page"),
    }
    # The CV windows on the desktops show the CV from the CV page's records.
    assert data["cv"]["name"] == "Dylan Fitzsimmons"
    assert data["cv"]["education"][0]["title"] == "MSc Software Development"
    assert set(data["images"]) == {"crt", "term", "lcd", "crtGlare", "termGlare", "lcdGlare"}
    for url in data["images"].values():
        assert finders.find(url.removeprefix(settings.STATIC_URL)) is not None, url


def test_list_works_as_a_plain_page(client: Client) -> None:
    response = client.get(reverse("projects:list"))

    assertContains(response, 'class="project-list"')
    assertContains(response, reverse("projects:detail", kwargs={"slug": "enular"}))


def test_detail_renders_the_write_up_as_safe_html(client: Client) -> None:
    body = "## How it works\n\n<script>alert(1)</script>"
    Project.objects.filter(slug="enular").update(body=body)

    response = client.get(reverse("projects:detail", kwargs={"slug": "enular"}))

    assertContains(response, 'id="how-it-works"')
    assertContains(response, 'href="#how-it-works"')
    assertNotContains(response, "<script>alert(1)</script>")


def test_detail_links_to_the_projects_either_side(client: Client) -> None:
    response = client.get(reverse("projects:detail", kwargs={"slug": "opus-equi"}))

    assert response.context["previous_project"].slug == "this-site"
    assert response.context["next_project"].slug == "enular"
    assertContains(response, reverse("projects:detail", kwargs={"slug": "enular"}))


def test_detail_goes_round_at_the_ends_of_the_list(client: Client) -> None:
    response = client.get(reverse("projects:detail", kwargs={"slug": "enular"}))

    assert response.context["previous_project"].slug == "opus-equi"
    assert response.context["next_project"].slug == "this-site"


def test_detail_says_so_when_there_is_no_write_up_yet(client: Client) -> None:
    Project.objects.filter(slug="enular").update(body="")

    response = client.get(reverse("projects:detail", kwargs={"slug": "enular"}))

    assertContains(response, "The write-up for this project is on its way.")


def test_detail_of_an_unpublished_project_is_not_found(client: Client) -> None:
    Project.objects.filter(slug="enular").update(is_published=False)

    response = client.get(reverse("projects:detail", kwargs={"slug": "enular"}))

    assert response.status_code == 404


def test_list_has_the_phone_desktop_with_a_window_for_each_project(client: Client) -> None:
    response = client.get(reverse("projects:list"))
    published = Project.objects.filter(is_published=True)

    assertContains(response, '<template id="desk-phone-template">')
    assertContains(response, "data-phone-project=", count=published.count())
    for index, project in enumerate(published):
        assertContains(response, f'data-phone-window="{index}"')
        assertContains(response, f'href="{project.get_absolute_url()}"')
    assertContains(response, "data-phone-exit")
