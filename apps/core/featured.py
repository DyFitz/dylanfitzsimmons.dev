"""The projects shown on the home page, each linking to its write-up on the projects page.

Fixed for now. The home page will take them from the projects app, as edited in the admin, once
its tests are set up to use the database.
"""

from dataclasses import dataclass
from enum import StrEnum

from django.urls import reverse


class Screen(StrEnum):
    """The animation on a project's card, and its still image for when motion is off."""

    SITE = "site"
    FORECAST = "forecast"
    BACKTEST = "backtest"


@dataclass(frozen=True, slots=True, kw_only=True)
class FeaturedProject:
    slug: str
    title: str
    summary: str
    tags: tuple[str, ...]
    screen: Screen
    in_progress: bool = False

    @property
    def still_template(self) -> str:
        return f"core/screens/{self.screen}.svg"

    @property
    def url(self) -> str:
        return reverse("projects:detail", kwargs={"slug": self.slug})


FEATURED_PROJECTS: tuple[FeaturedProject, ...] = (
    FeaturedProject(
        slug="this-site",
        title="This site",
        summary=(
            "A Django site for my projects, CV and investments, built with tests, CI and Docker "
            "from the first commit."
        ),
        tags=("Django", "PostgreSQL", "Docker"),
        screen=Screen.SITE,
        in_progress=True,
    ),
    FeaturedProject(
        slug="opus-equi",
        title="Opus Equi",
        summary=(
            "Probabilistic price forecasting: a C#/.NET 8 desktop app over a Python FastAPI "
            "service. My MSc dissertation."
        ),
        tags=("Python", "FastAPI", "C#", "WPF"),
        screen=Screen.FORECAST,
    ),
    FeaturedProject(
        slug="enular",
        title="Enular",
        summary=(
            "A fintech startup I co-founded, and its backtesting engine: an open-source Python "
            "package on PyPI, built on Backtrader."
        ),
        tags=("Python", "Backtrader"),
        screen=Screen.BACKTEST,
    ),
)
