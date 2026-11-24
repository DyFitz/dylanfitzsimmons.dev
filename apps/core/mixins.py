from typing import Any

from django.views.generic.base import ContextMixin


class PageMetaMixin(ContextMixin):
    """Title, description and preview image for <title>, the meta description and Open Graph tags.

    Left empty, they fall back to the site defaults. Detail views can override
    the getters to describe the object being shown. page_image is a path under static/, shown
    when a link to the page is shared.
    """

    page_title: str = ""
    page_description: str = ""
    page_image: str = ""

    def get_page_title(self) -> str:
        return self.page_title

    def get_page_description(self) -> str:
        return self.page_description

    def get_page_image(self) -> str:
        return self.page_image

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.get_page_title()
        context["page_description"] = self.get_page_description()
        context["page_image"] = self.get_page_image()
        return context
