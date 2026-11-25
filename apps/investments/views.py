from django.core.cache import cache
from django.utils import timezone
from django.views.generic import TemplateView

from apps.core.mixins import PageMetaMixin
from apps.investments import report
from apps.investments.history import load
from apps.investments.models import Day, ImportRun, Instrument, Portfolio
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
        latest = Day.objects.order_by("-date").values_list("date", flat=True).first()
        if self.portfolio is None or latest is None:
            return None
        today = timezone.localdate()
        run = ImportRun.objects.order_by("-pk").values_list("pk", flat=True).first()
        # The figures change with an import, with the day (the status line), and with the
        # sleeves, sectors and targets set in the admin.
        plan = hash(
            tuple(Instrument.objects.values_list("pk", "sleeve", "sector", "target_weight"))
        )
        key = f"investments:{latest}:{run}:{today}:{plan}:{self.portfolio.cash_target}"
        figures = cache.get(key)
        if figures is None:
            history = load()
            figures = report.build(history, self.portfolio, today) if history else None
            cache.set(key, figures, 60 * 60 * 24)
        return figures

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.figures is not None:
            context |= self.figures
            context["thinking"] = [
                ("The idea", render_markdown(self.portfolio.idea)),
                ("Why these holdings", render_markdown(self.portfolio.holdings)),
                ("The rules", render_markdown(self.portfolio.rules)),
            ]
        return context
