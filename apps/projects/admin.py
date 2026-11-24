from typing import ClassVar

from django.contrib import admin

from apps.projects.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "year", "position", "is_published")
    list_editable = ("position", "is_published")
    prepopulated_fields: ClassVar[dict[str, tuple[str, ...]]] = {"slug": ("title",)}
    search_fields = ("title", "summary", "stack")
