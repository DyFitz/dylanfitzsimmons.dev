import re

import pytest
from django.test import Client
from django.urls import reverse

from apps.core.tests.html import start_tags

INLINE_SCRIPT = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>", re.IGNORECASE)

PAGES = [pytest.param("/", id="home"), pytest.param("/no-such-page/", id="not-found")]


def test_content_security_policy_is_enforced(client: Client) -> None:
    policy = client.get(reverse("core:home"))["Content-Security-Policy"]

    assert "default-src 'self'" in policy
    assert "frame-ancestors 'none'" in policy
    assert "object-src 'none'" in policy
    assert "unsafe-inline" not in policy


@pytest.mark.parametrize("path", PAGES)
def test_pages_contain_no_inline_scripts(client: Client, path: str) -> None:
    # The CSP blocks inline scripts, so any here would silently fail.
    html = client.get(path).content.decode()

    assert INLINE_SCRIPT.findall(html) == []


@pytest.mark.parametrize("path", PAGES)
def test_pages_contain_no_inline_styles(client: Client, path: str) -> None:
    # The CSP blocks these too. Styles belong in main.css, and scripts set them through the DOM.
    html = client.get(path).content.decode()

    assert start_tags(html, "style") == []
    assert [attrs for attrs in start_tags(html) if "style" in attrs] == []


def test_standard_security_headers_are_set(client: Client) -> None:
    response = client.get(reverse("core:home"))

    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["X-Frame-Options"] == "DENY"
    assert response["Referrer-Policy"] == "same-origin"
    assert response["Cross-Origin-Opener-Policy"] == "same-origin"
