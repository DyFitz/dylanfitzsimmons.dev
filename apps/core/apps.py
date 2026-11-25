from django.apps import AppConfig
from django.contrib.admin import apps as admin_apps


class CoreConfig(AppConfig):
    # The app's own config; the admin's below is named in INSTALLED_APPS.
    default = True
    name = "apps.core"
    label = "core"
    verbose_name = "Core"

    def ready(self) -> None:
        # Registers the system checks.
        from apps.core import checks  # noqa: F401


class SiteAdminConfig(admin_apps.AdminConfig):
    """The admin, on the site's own admin site, which adds two-factor login."""

    default = False
    default_site = "apps.core.admin_site.SiteAdmin"
