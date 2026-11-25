import pytest
from django.template import Context, Template

from apps.core.links import leaves_site, open_away_links_in_new_tabs
from apps.projects.markdown import render_markdown


@pytest.mark.parametrize(
    ("url", "leaves"),
    [
        ("https://github.com/DyFitz", True),
        ("http://example.com/page", True),
        ("/static/files/opus-equi-dissertation.pdf", True),
        ("/projects/this-site/", False),
        ("#how-it-works", False),
        ("mailto:someone@example.com", False),
        ("https://dylanfitzsimmons.dev/cv/", False),
    ],
)
def test_which_links_leave_the_site(settings, url, leaves):
    settings.SITE_URL = "https://dylanfitzsimmons.dev"
    assert leaves_site(url) is leaves


def test_write_up_links_that_leave_open_in_a_new_tab(settings):
    settings.SITE_URL = "https://dylanfitzsimmons.dev"
    html = render_markdown("[GitHub](https://github.com/DyFitz) and [the CV](/cv/).")
    assert (
        '<a href="https://github.com/DyFitz" target="_blank" rel="noopener noreferrer">GitHub'
        '<span class="visually-hidden"> (opens in a new tab)</span></a>'
    ) in html
    assert '<a href="/cv/">the CV</a>' in html


def test_a_link_with_its_own_target_is_left_alone():
    html = '<a href="https://x.test" target="_self">x</a>'
    assert open_away_links_in_new_tabs(html) == html


def test_the_template_tags():
    rendered = Template(
        '{% load links %}<a href="https://x.test"{% new_tab %}>x{% new_tab_note %}</a>'
    ).render(Context())
    assert rendered == (
        '<a href="https://x.test" target="_blank" rel="noopener noreferrer">x'
        '<span class="visually-hidden"> (opens in a new tab)</span></a>'
    )
