from typing import Any

from django.views.generic import TemplateView

from apps.core.mixins import PageMetaMixin
from apps.cv.content import cv_context

# The CV's sections, for the index in the ID card and the jump strip on narrower screens.
SECTIONS = [
    {"id": section_id, "number": f"{number:02d}", "label": section_id.capitalize()}
    for number, section_id in enumerate(
        ("profile", "education", "experience", "projects", "skills"), start=1
    )
]


class CvView(PageMetaMixin, TemplateView):
    template_name = "cv/cv.html"
    page_title = "CV"
    page_description = (
        "Education, experience, projects and skills, with a one-page PDF to download."
    )
    page_image = "img/og/cv.jpg"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(cv_context())
        context["sections"] = SECTIONS
        return context
