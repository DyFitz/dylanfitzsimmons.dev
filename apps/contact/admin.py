from django.contrib import admin
from django.http import HttpRequest

from apps.contact.models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Messages are a record of what was sent, so they can be read and deleted but not changed."""

    list_display = ("reference", "name", "email", "reason", "sent_at", "emailed")
    list_filter = ("reason", "emailed", "sent_at")
    search_fields = ("name", "email", "body")
    date_hierarchy = "sent_at"
    fields = ("name", "email", "reason", "sent_at", "emailed", "body")

    @admin.display(description="ref", ordering="pk")
    def reference(self, message: Message) -> str:
        return message.reference

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Message | None = None) -> bool:
        return False
