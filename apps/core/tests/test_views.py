from django.test import Client, RequestFactory
from django.urls import reverse
from django.views.defaults import server_error
from pytest_django import Settings
from pytest_django.asserts import assertContains, assertNotContains, assertTemplateUsed

from apps.core.featured import FEATURED_PROJECTS
from apps.core.tests.html import start_tags


def test_home_page_shows_the_site_identity(client: Client, settings: Settings) -> None:
    settings.SITE_NAME = "Ada Lovelace"
    settings.SITE_TAGLINE = "Analyst"

    response = client.get(reverse("core:home"))

    assert response.status_code == 200
    assertTemplateUsed(response, "core/home.html")
    assertContains(response, "<title>Ada Lovelace \N{EN DASH} Analyst</title>", html=True)
    assertContains(response, '<h1 class="hero__name" id="hero-name">Ada Lovelace</h1>', html=True)


def test_home_page_declares_its_canonical_url_and_description(
    client: Client, settings: Settings
) -> None:
    settings.SITE_URL = "https://example.com"
    settings.SITE_DESCRIPTION = "A test description."

    response = client.get(reverse("core:home"))

    assertContains(response, '<link rel="canonical" href="https://example.com/">', html=True)
    assertContains(response, '<meta name="description" content="A test description.">', html=True)


def test_home_page_shows_the_featured_projects(client: Client) -> None:
    response = client.get(reverse("core:home"))

    for project in FEATURED_PROJECTS:
        assertContains(response, project.title)
        assertContains(response, project.summary)
        for tag in project.tags:
            assertContains(response, f'<li class="tag">{tag}</li>', html=True)


def test_each_project_card_links_to_its_write_up(client: Client) -> None:
    response = client.get(reverse("core:home"))

    for project in FEATURED_PROJECTS:
        url = reverse("projects:detail", kwargs={"slug": project.slug})
        assertContains(response, f'class="project-card__link" href="{url}"')
    assertContains(response, f'href="{reverse("projects:list")}"')


def test_contact_panel_links_to_the_contact_page(client: Client) -> None:
    response = client.get(reverse("core:home"))

    assertContains(response, f'href="{reverse("contact:page")}">Send a message</a>')


def test_every_animation_on_the_home_page_has_a_still_version(client: Client) -> None:
    html = client.get(reverse("core:home")).content.decode()

    project_screens = [attrs for attrs in start_tags(html, "canvas") if "data-screen" in attrs]
    stills = [attrs for attrs in start_tags(html, "svg") if "still" in (attrs.get("class") or "")]
    images = {attrs.get("src") or "" for attrs in start_tags(html, "img")}

    assert len(project_screens) == len(FEATURED_PROJECTS)
    assert len(stills) == len(FEATURED_PROJECTS)
    assert any(src.endswith("/img/globe.svg") for src in images)
    assert any(src.endswith("/img/code-rain.svg") for src in images)


def test_console_shows_its_first_script_without_javascript(client: Client) -> None:
    html = client.get(reverse("core:home")).content.decode()

    scripts = [attrs for attrs in start_tags(html, "ol") if "data-console-script" in attrs]

    assert len(scripts) > 1
    assert "hidden" not in scripts[0]
    assert all("hidden" in attrs for attrs in scripts[1:])


def test_controls_that_need_javascript_start_hidden(client: Client) -> None:
    html = client.get(reverse("core:home")).content.decode()

    wired_by_javascript = {"data-motion-toggle", "data-intro-replay", "data-theme-toggle"}
    controls = [attrs for attrs in start_tags(html, "button") if attrs.keys() & wired_by_javascript]

    assert len(controls) == 3
    assert all("hidden" in attrs for attrs in controls)


def test_only_the_home_page_has_an_intro(client: Client) -> None:
    home = client.get(reverse("core:home")).content.decode()
    missing = client.get("/no-such-page/").content.decode()

    assert start_tags(home, "html")[0].get("data-intro") == "available"
    assert "data-intro" not in start_tags(missing, "html")[0]


def test_hero_shows_the_sites_domain(client: Client, settings: Settings) -> None:
    settings.SITE_URL = "https://example.com"

    response = client.get(reverse("core:home"))

    assertContains(response, "uplink: example.com")


def test_footer_links_to_the_deployed_commit(client: Client, settings: Settings) -> None:
    settings.SITE_SOURCE_URL = "https://github.com/example/site"
    settings.GIT_SHA = "0123456789abcdef0123456789abcdef01234567"

    response = client.get(reverse("core:home"))

    assertContains(
        response,
        '<a href="https://github.com/example/site/commit/0123456789abcdef0123456789abcdef01234567">'
        "<code>0123456</code></a>",
        html=True,
    )


def test_footer_leaves_out_build_details_when_the_commit_is_unknown(
    client: Client, settings: Settings
) -> None:
    settings.GIT_SHA = ""

    response = client.get(reverse("core:home"))

    assertNotContains(response, "site-footer__build")


def test_robots_txt_is_served_as_plain_text(client: Client) -> None:
    response = client.get(reverse("core:robots_txt"))

    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain; charset=utf-8"
    assert response.content.decode().startswith("User-agent: *")


def test_unknown_pages_use_the_custom_404_template(client: Client) -> None:
    response = client.get("/no-such-page/")

    assertTemplateUsed(response, "404.html")
    assertContains(response, "Page not found", status_code=404)


def test_server_error_page_renders_without_request_context(rf: RequestFactory) -> None:
    # Django renders 500.html without context processors.
    response = server_error(rf.get("/"))

    assert response.status_code == 500
    assert b"Something went wrong" in response.content
