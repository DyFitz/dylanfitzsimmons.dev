from typing import ClassVar

from django.db import models
from django.urls import reverse

# The short codes the terminal screen shows in its State column.
STATUS_CODES = {
    "in progress": "WIP",
    "complete": "DONE",
    "live": "LIVE",
    "archived": "ARCH",
}


class Project(models.Model):
    """A project on the projects page, with its write-up."""

    class Screen(models.TextChoices):
        """The animated preview shown for the project, and its still image."""

        SITE = "site", "A web page being drawn"
        FORECAST = "forecast", "A forecast chart"
        BACKTEST = "backtest", "A backtest chart"

    title = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    summary = models.CharField(max_length=200)
    stack = models.CharField(
        max_length=200, help_text="What it's built with, separated by commas, main one first."
    )
    role = models.CharField(max_length=120, blank=True)
    period = models.CharField(
        max_length=40,
        blank=True,
        # The dash between the years is an en dash, on purpose.
        help_text='For example "2024 – 2025".',  # noqa: RUF001
    )
    year = models.CharField(max_length=10, blank=True, help_text="The year shown in the list.")
    status = models.CharField(
        max_length=30,
        blank=True,
        help_text='For example "In progress", "Complete", "Live" or "Archived".',
    )
    screen = models.CharField(max_length=20, choices=Screen, default=Screen.SITE)
    body = models.TextField(blank=True, help_text="The write-up, in Markdown.")
    repo_url = models.URLField("repository URL", blank=True)
    position = models.PositiveSmallIntegerField(
        default=0, help_text="Lower numbers come first in the list."
    )
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["position", "title"]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("projects:detail", kwargs={"slug": self.slug})

    @property
    def still_template(self) -> str:
        """The still image that stands in for the animated preview when motion is off."""
        return f"core/screens/{self.screen}.svg"

    @property
    def tags(self) -> list[str]:
        return [tag.strip() for tag in self.stack.split(",") if tag.strip()]

    @property
    def short_stack(self) -> str:
        """The main tool and how many others, e.g. "Django +2", for narrow columns."""
        tags = self.tags
        if len(tags) <= 1:
            return "".join(tags)
        return f"{tags[0]} +{len(tags) - 1}"

    @property
    def status_code(self) -> str:
        return STATUS_CODES.get(self.status.strip().lower(), "[?]")
