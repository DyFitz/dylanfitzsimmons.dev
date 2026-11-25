from django.views.generic import TemplateView

from apps.core.mixins import PageMetaMixin
from apps.investments.figures import figures
from apps.investments.models import Portfolio
from apps.projects.markdown import render_markdown


class InvestmentsView(PageMetaMixin, TemplateView):
    """The portfolio, or a notice that it's being built until there's any history."""

    page_title = "Investments"
    page_description = (
        "A portfolio built around AI's demand for chips and memory: returns, risk and "
        "holdings, updated at the end of each day."
    )
    page_image = "img/og/investments.jpg"

    def get(self, request, *args, **kwargs):
        self.portfolio = Portfolio.load()
        self.figures = self.build()
        return super().get(request, *args, **kwargs)

    def get_template_names(self) -> list[str]:
        if self.figures is None:
            return ["investments/investments.html"]
        return ["investments/dashboard.html"]

    def build(self) -> dict | None:
        return figures(self.portfolio)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.figures is not None:
            context |= self.figures
            context["thinking"] = [
                ("The idea", render_markdown(self.portfolio.idea)),
                ("Why these holdings", render_markdown(self.portfolio.holdings)),
                ("The rules", render_markdown(self.portfolio.rules)),
            ]
            if self.portfolio.measured:
                context["measured"] = render_markdown(self.portfolio.measured)
        return context
