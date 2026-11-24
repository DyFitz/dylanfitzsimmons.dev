from typing import Any

from django.db.models import QuerySet
from django.templatetags.static import static
from django.urls import reverse
from django.views.generic import DetailView, ListView

from apps.core.mixins import PageMetaMixin
from apps.cv.content import cv_summary
from apps.projects.markdown import render_write_up
from apps.projects.models import Project

# The photographs of the three monitors, in static/img/projects.
MONITOR_PHOTOS = ("crt", "term", "lcd")


def desk_data(projects: list[Project]) -> dict[str, Any]:
    """What the projects page's script needs to put the projects on the monitors."""
    home = reverse("core:home")
    return {
        "urls": {"home": home, "cv": reverse("cv:page"), "contact": reverse("contact:page")},
        "images": {
            **{name: static(f"img/projects/{name}.webp") for name in MONITOR_PHOTOS},
            # The reflections laid over each screen.
            **{
                f"{name}Glare": static(f"img/projects/{name}-glare.webp") for name in MONITOR_PHOTOS
            },
        },
        # For the CV windows on the desktops.
        "cv": cv_summary(),
        "projects": [
            {
                "slug": project.slug,
                "title": project.title,
                "summary": project.summary,
                "tags": project.tags,
                "role": project.role,
                "when": project.period,
                "year": project.year,
                "status": project.status,
                "code": project.status_code,
                "screen": project.screen,
                "href": project.get_absolute_url(),
            }
            for project in projects
        ],
    }


class ProjectListView(PageMetaMixin, ListView):
    template_name = "projects/project_list.html"
    context_object_name = "projects"
    page_title = "Projects"
    page_description = (
        "Software projects, each with a write-up of how it works and what was learned "
        "along the way."
    )

    def get_queryset(self) -> QuerySet[Project]:
        return Project.objects.filter(is_published=True)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["desk_data"] = desk_data(list(context["projects"]))
        return context


class ProjectDetailView(PageMetaMixin, DetailView):
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_queryset(self) -> QuerySet[Project]:
        return Project.objects.filter(is_published=True)

    def get_page_title(self) -> str:
        return self.object.title

    def get_page_description(self) -> str:
        return self.object.summary

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["write_up"] = render_write_up(self.object.body)
        # The projects either side of this one in the list, going round at the ends.
        published = list(self.get_queryset())
        if len(published) > 1:
            index = published.index(self.object)
            context["previous_project"] = published[index - 1]
            context["next_project"] = published[(index + 1) % len(published)]
        return context
