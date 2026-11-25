"""Links that leave the site open in a new tab, so the page they came from stays open behind
them. A note for screen readers says so, as a new tab is otherwise easy to miss. PDFs count as
leaving: a browser opens them in its own viewer."""

import re
from urllib.parse import urlsplit

from django.conf import settings

NEW_TAB = ' target="_blank" rel="noopener noreferrer"'
NOTE = '<span class="visually-hidden"> (opens in a new tab)</span>'

# An opening <a> tag, its href, and what follows up to its closing tag. Only for HTML the
# Markdown renderer has just cleaned, whose tags it writes in a known form.
ANCHOR = re.compile(r'<a href="(?P<href>[^"]*)"(?P<rest>[^>]*)>(?P<text>.*?)</a>', re.DOTALL)


def leaves_site(url: str) -> bool:
    """Whether a link goes to another site or to a document."""
    parts = urlsplit(url)
    if parts.path.lower().endswith(".pdf"):
        return True
    if parts.scheme not in ("http", "https"):
        return False
    return parts.netloc.lower() != urlsplit(settings.SITE_URL).netloc.lower()


def open_away_links_in_new_tabs(html: str) -> str:
    def mark(match: re.Match) -> str:
        if not leaves_site(match["href"]) or "target=" in match["rest"]:
            return match[0]
        rest = re.sub(r'\s*rel="[^"]*"', "", match["rest"])
        return f'<a href="{match["href"]}"{rest}{NEW_TAB}>{match["text"]}{NOTE}</a>'

    return ANCHOR.sub(mark, html)
