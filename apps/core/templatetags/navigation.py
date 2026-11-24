from django.template import Context, Library

from apps.core.navigation import NavLink, build_navigation

register = Library()


@register.inclusion_tag("includes/main_nav.html", takes_context=True)
def main_nav(context: Context) -> dict[str, list[NavLink]]:
    request = context.get("request")
    current_path = request.path if request is not None else ""
    return {"links": build_navigation(current_path)}
