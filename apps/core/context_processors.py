from django.http import HttpRequest

from apps.core.site import SiteConfig


def site(request: HttpRequest) -> dict[str, SiteConfig]:
    return {"site": SiteConfig.from_settings()}
