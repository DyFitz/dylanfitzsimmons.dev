from django.contrib import admin
from django.http import HttpRequest

from apps.cv.models import CvProject, Entry, Evidence, Profile, Readout, Skill, SkillGroup


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "updated")

    def has_add_permission(self, request: HttpRequest) -> bool:
        # The CV has one profile; it's edited, not added to.
        return not Profile.objects.exists() and super().has_add_permission(request)


@admin.register(Readout)
class ReadoutAdmin(admin.ModelAdmin):
    list_display = ("value", "label", "position")
    list_editable = ("position",)


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("title", "organisation", "kind", "started", "ended", "position")
    list_editable = ("position",)
    list_filter = ("kind",)


@admin.register(CvProject)
class CvProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "meta", "is_key", "position")
    list_editable = ("is_key", "position")


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 0


@admin.register(SkillGroup)
class SkillGroupAdmin(admin.ModelAdmin):
    list_display = ("title", "position")
    list_editable = ("position",)
    inlines = (SkillInline,)


class EvidenceInline(admin.TabularInline):
    model = Evidence
    extra = 0


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "position")
    list_filter = ("group",)
    inlines = (EvidenceInline,)
