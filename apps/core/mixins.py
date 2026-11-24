from typing import Any

from django.views.generic.base import ContextMixin


class PageMetaMixin(ContextMixin):
    """Title and description for <title>, the meta description and Open Graph tags.

    Left empty, they fall back to the site defaults. Detail views can override
    the getters to describe the object being shown.
    """

    page_title: str = ""
    page_description: str = ""

    def get_page_title(self) -> str:
        return self.page_title

    def get_page_description(self) -> str:
        return self.page_description

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.get_page_title()
        context["page_description"] = self.get_page_description()
        return context
