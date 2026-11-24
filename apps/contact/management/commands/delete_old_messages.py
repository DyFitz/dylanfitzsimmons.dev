from typing import Any

from django.core.management.base import BaseCommand

from apps.contact.models import Message


class Command(BaseCommand):
    help = "Delete contact messages older than 12 months. Meant to run daily on a schedule."

    def handle(self, *args: Any, **options: Any) -> None:
        deleted, _ = Message.objects.expired().delete()
        self.stdout.write(f"Deleted {deleted} message{'' if deleted == 1 else 's'}.")
