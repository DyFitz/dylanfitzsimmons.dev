from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.db.models import QuerySet
from django.urls import reverse

from apps.projects.models import Project


class SiteSitemap(Sitemap):
    """A sitemap whose addresses come from SITE_URL rather than the request.

    Behind the hosting platform's proxy, the request can carry an internal host name, and the
    sitemap must only ever list the public one.
    """

    def get_protocol(self, protocol: str | None = None) -> str:
        return urlsplit(settings.SITE_URL).scheme

    def get_domain(self, site: object = None) -> str:
        return urlsplit(settings.SITE_URL).netloc


class PageSitemap(SiteSitemap):
    """The site's main pages, in the order of the navigation."""

    def items(self) -> list[str]:
        return [
            "core:home",
            "projects:list",
            "cv:page",
            "contact:page",
            "investments:page",
        ]

    def location(self, item: str) -> str:
        return reverse(item)


class ProjectSitemap(SiteSitemap):
    """Each published project's write-up."""

    def items(self) -> QuerySet[Project]:
        return Project.objects.filter(is_published=True)


SITEMAPS = {"pages": PageSitemap, "projects": ProjectSitemap}
