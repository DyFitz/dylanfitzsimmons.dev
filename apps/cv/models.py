from typing import ClassVar

from django.db import models
from django.utils.safestring import SafeString

from apps.projects.markdown import render_markdown


def lines(text: str) -> list[str]:
    """One item per non-empty line, for the bullet points kept in a text box."""
    return [line.strip() for line in text.splitlines() if line.strip()]


class Profile(models.Model):
    """The top of the CV and the ID card beside it. There is only ever one."""

    name = models.CharField(max_length=80)
    role = models.CharField(max_length=120, help_text='For example "Software developer · Glasgow".')
    looking_for = models.CharField(
        max_length=200, help_text="What I'm looking for, on the ID card."
    )
    summary = models.TextField(help_text="The profile paragraph.")
    github_url = models.URLField("GitHub URL", blank=True)
    linkedin_url = models.URLField("LinkedIn URL", blank=True)
    updated = models.DateField(help_text="When the CV was last brought up to date.")

    class Meta:
        verbose_name = "profile"

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def link_text(url: str) -> str:
        """A URL as it reads on the page: github.com/DyFitz, not https://github.com/DyFitz/."""
        return url.removeprefix("https://").removeprefix("http://").removeprefix("www.").rstrip("/")

    @property
    def github_text(self) -> str:
        return self.link_text(self.github_url)

    @property
    def linkedin_text(self) -> str:
        return self.link_text(self.linkedin_url)


class Readout(models.Model):
    """One of the three facts at a glance under the profile."""

    value = models.CharField(max_length=40)
    label = models.CharField(max_length=120)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering: ClassVar[list[str]] = ["position"]

    def __str__(self) -> str:
        return self.value


class Entry(models.Model):
    """A degree or a job, on the timeline."""

    class Kind(models.TextChoices):
        EDUCATION = "education", "Education"
        EXPERIENCE = "experience", "Experience"

    kind = models.CharField(max_length=20, choices=Kind)
    title = models.CharField(max_length=120)
    organisation = models.CharField(max_length=120)
    started = models.CharField(max_length=20, help_text='For example "Sep 2024".')
    ended = models.CharField(
        max_length=20, blank=True, help_text="Left empty while it's still going."
    )
    summary = models.TextField(blank=True)
    points = models.TextField(blank=True, help_text="Bullet points, one per line.")
    more = models.TextField(
        blank=True,
        help_text='Shown when "More" is opened, in Markdown. Empty means no "More".',
    )
    award = models.CharField(max_length=160, blank=True)
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text='A project write-up to link to from "More".',
    )
    position = models.PositiveSmallIntegerField(default=0, help_text="Lower numbers come first.")

    class Meta:
        ordering: ClassVar[list[str]] = ["kind", "position"]
        verbose_name_plural = "entries"

    def __str__(self) -> str:
        return f"{self.title}, {self.organisation}"

    @property
    def is_current(self) -> bool:
        return not self.ended

    @property
    def point_list(self) -> list[str]:
        return lines(self.points)

    @property
    def more_html(self) -> SafeString:
        return render_markdown(self.more)


class CvProject(models.Model):
    """A project as the CV lists it. The key one gets the wider card."""

    title = models.CharField(max_length=120)
    meta = models.CharField(
        max_length=60, blank=True, help_text='For example "MSc dissertation · 2025".'
    )
    stack = models.CharField(max_length=200, blank=True, help_text="Separated by commas.")
    summary = models.TextField(blank=True)
    points = models.TextField(blank=True, help_text="Bullet points shown at first, one per line.")
    more_points = models.TextField(
        blank=True, help_text='Bullet points under "More", one per line.'
    )
    write_up = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="The project's write-up on the projects page, if it has one.",
    )
    is_key = models.BooleanField(default=False)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering: ClassVar[list[str]] = ["-is_key", "position"]
        verbose_name = "CV project"

    def __str__(self) -> str:
        return self.title

    @property
    def stack_list(self) -> list[str]:
        return [part.strip() for part in self.stack.split(",") if part.strip()]

    @property
    def point_list(self) -> list[str]:
        return lines(self.points)

    @property
    def more_point_list(self) -> list[str]:
        return lines(self.more_points)


class SkillGroup(models.Model):
    title = models.CharField(max_length=60)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering: ClassVar[list[str]] = ["position"]

    def __str__(self) -> str:
        return self.title


class Skill(models.Model):
    group = models.ForeignKey(SkillGroup, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=80)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering: ClassVar[list[str]] = ["position"]

    def __str__(self) -> str:
        return self.name


class Evidence(models.Model):
    """Where a skill was used, linked to a project's write-up where there is one."""

    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="evidence")
    label = models.CharField(max_length=80)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering: ClassVar[list[str]] = ["position"]
        verbose_name_plural = "evidence"

    def __str__(self) -> str:
        return self.label
