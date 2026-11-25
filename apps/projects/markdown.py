import re
from dataclasses import dataclass

import markdown
import nh3
from django.utils.safestring import SafeString, mark_safe
from django.utils.text import slugify

from apps.core.links import open_away_links_in_new_tabs

# A second-level heading: "## Like this", with or without closing hashes.
SECTION_HEADING = re.compile(r"^##\s+(?P<title>.+?)\s*#*\s*$")
CODE_FENCES = ("```", "~~~")


@dataclass(frozen=True, slots=True)
class Section:
    """One headed part of a write-up."""

    title: str
    # The id the page gives the section, for links to it.
    anchor: str
    html: SafeString


@dataclass(frozen=True, slots=True)
class WriteUp:
    """A write-up as the project page shows it: an opening, then numbered sections."""

    # Anything written before the first heading.
    intro: SafeString
    sections: tuple[Section, ...]


def render_markdown(text: str) -> SafeString:
    """Turn a Markdown write-up into HTML that is safe to put in a page.

    The HTML is cleaned after conversion, so raw HTML in the Markdown can't bring in scripts
    or anything else the page shouldn't carry.
    """
    html = markdown.markdown(text, extensions=["fenced_code", "tables"])
    return mark_safe(open_away_links_in_new_tabs(nh3.clean(html)))  # noqa: S308


def render_write_up(text: str) -> WriteUp:
    """Split a write-up at its second-level headings and render each part.

    The headings become the page's numbered sections and its list of contents. A line that
    looks like a heading inside a block of code is left alone.
    """
    parts: list[tuple[str, list[str]]] = [("", [])]
    in_code = False
    for line in text.splitlines():
        if line.lstrip().startswith(CODE_FENCES):
            in_code = not in_code
        heading = None if in_code else SECTION_HEADING.match(line)
        if heading:
            parts.append((heading["title"], []))
        else:
            parts[-1][1].append(line)

    intro = render_markdown("\n".join(parts[0][1]).strip())
    sections = []
    anchors: set[str] = set()
    for number, (title, lines) in enumerate(parts[1:], start=1):
        # Two sections with the same heading still need ids of their own.
        anchor = slugify(title) or f"section-{number}"
        if anchor in anchors:
            anchor = f"{anchor}-{number}"
        anchors.add(anchor)
        sections.append(
            Section(title=title, anchor=anchor, html=render_markdown("\n".join(lines).strip()))
        )
    return WriteUp(intro=intro, sections=tuple(sections))
