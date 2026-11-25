from django import template
from django.utils.safestring import SafeString, mark_safe

from apps.core.links import NEW_TAB, NOTE

register = template.Library()


@register.simple_tag
def new_tab() -> SafeString:
    """The attributes for a link that leaves the site: <a href="…"{% new_tab %}>."""
    return mark_safe(NEW_TAB)  # noqa: S308 - a fixed string


@register.simple_tag
def new_tab_note() -> SafeString:
    """Tells screen readers the link opens a new tab; goes inside the link."""
    return mark_safe(NOTE)  # noqa: S308 - a fixed string
