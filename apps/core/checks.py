from collections.abc import Sequence

from django.apps import AppConfig
from django.conf import settings
from django.core import checks

DEFAULT_ADMIN_URL = "admin/"


@checks.register(checks.Tags.urls)
def check_admin_url_format(
    app_configs: Sequence[AppConfig] | None, **kwargs: object
) -> list[checks.CheckMessage]:
    """ADMIN_URL is used as a path prefix, so it needs a trailing slash and no leading one."""
    admin_url = settings.ADMIN_URL
    if admin_url.endswith("/") and not admin_url.startswith("/"):
        return []
    return [
        checks.Error(
            f"ADMIN_URL must end with '/' and must not start with '/' (got {admin_url!r}).",
            hint="Set DJANGO_ADMIN_URL to a value such as 'manage-7f3a/'.",
            id="core.E001",
        )
    ]


@checks.register(checks.Tags.security, deploy=True)
def check_admin_url_is_not_default(
    app_configs: Sequence[AppConfig] | None, **kwargs: object
) -> list[checks.CheckMessage]:
    """Bots constantly probe /admin/, so production should use another path."""
    if settings.ADMIN_URL != DEFAULT_ADMIN_URL:
        return []
    return [
        checks.Warning(
            "The admin is served at the default /admin/ path.",
            hint="Set DJANGO_ADMIN_URL to a less guessable path in production.",
            id="core.W001",
        )
    ]
