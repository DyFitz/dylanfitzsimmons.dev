from django.views.generic import TemplateView

from apps.core.mixins import PageMetaMixin


class InvestmentsView(PageMetaMixin, TemplateView):
    """A placeholder until the portfolio is built: the page is linked, but says so."""

    template_name = "investments/investments.html"
    page_title = "Investments"
    page_description = "The investment portfolio and the strategy behind it. In progress."
    page_image = "img/og/investments.jpg"
