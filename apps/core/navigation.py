from dataclasses import dataclass

from django.urls import reverse


@dataclass(frozen=True, slots=True)
class NavItem:
    label: str
    url_name: str
    icon: str  # the drawing used on the phone's tab bar, from includes/nav_icon.html


@dataclass(frozen=True, slots=True)
class NavLink:
    """A NavItem resolved for the current page."""

    label: str
    url: str
    aria_current: str | None
    icon: str


PRIMARY_NAVIGATION: tuple[NavItem, ...] = (
    NavItem(label="Home", url_name="core:home", icon="home"),
    NavItem(label="Projects", url_name="projects:list", icon="projects"),
    NavItem(label="Investments", url_name="investments:page", icon="investments"),
    NavItem(label="CV", url_name="cv:page", icon="cv"),
    NavItem(label="Contact", url_name="contact:page", icon="contact"),
)


def aria_current(link_url: str, current_path: str) -> str | None:
    """Return the aria-current value for a nav link, or None.

    "page" on an exact match, and "true" anywhere else in that section, e.g. the
    Projects link on /projects/this-site/. Home only matches itself, otherwise
    it would match every page.
    """
    if current_path == link_url:
        return "page"
    if link_url != "/" and current_path.startswith(link_url):
        return "true"
    return None


def build_navigation(current_path: str) -> list[NavLink]:
    links = []
    for item in PRIMARY_NAVIGATION:
        url = reverse(item.url_name)
        links.append(
            NavLink(
                label=item.label,
                url=url,
                aria_current=aria_current(url, current_path),
                icon=item.icon,
            )
        )
    return links
