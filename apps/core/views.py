from typing import Any

from django.views.generic import TemplateView

from apps.core.featured import FEATURED_PROJECTS
from apps.core.mixins import PageMetaMixin


class HomeView(PageMetaMixin, TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["featured_projects"] = FEATURED_PROJECTS
        return context


class RobotsTxtView(TemplateView):
    template_name = "robots.txt"
    content_type = "text/plain; charset=utf-8"
