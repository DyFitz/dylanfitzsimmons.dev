from datetime import timedelta
from typing import ClassVar

from django.db import models
from django.utils import timezone

# How long messages are kept, as the privacy note on the contact page says.
RETENTION = timedelta(days=365)


class MessageQuerySet(models.QuerySet["Message"]):
    def expired(self) -> MessageQuerySet:
        """Messages older than the retention period, due to be deleted."""
        return self.filter(sent_at__lt=timezone.now() - RETENTION)

    def recent_from(self, sender_hash: str, within: timedelta) -> MessageQuerySet:
        return self.filter(sender_hash=sender_hash, sent_at__gte=timezone.now() - within)


class Message(models.Model):
    """A message sent through the contact form."""

    class Reason(models.TextChoices):
        JOB = "job", "Job opportunity"
        PROJECT = "project", "Project or freelance"
        OTHER = "other", "Something else"

    name = models.CharField(max_length=100)
    email = models.EmailField("reply-to address")
    reason = models.CharField(max_length=20, choices=Reason, default=Reason.JOB)
    body = models.TextField("message")
    sent_at = models.DateTimeField(default=timezone.now, db_index=True)
    # A keyed hash of the sender's IP address, never the address itself. It's only used to
    # limit how many messages one sender can send in an hour.
    sender_hash = models.CharField(max_length=64, blank=True, db_index=True, editable=False)
    emailed = models.BooleanField(
        default=False, help_text="Whether the email about it went out. It's saved either way."
    )

    objects = MessageQuerySet.as_manager()

    class Meta:
        ordering: ClassVar[list[str]] = ["-sent_at"]

    def __str__(self) -> str:
        return f"{self.reference} from {self.name}"

    @property
    def reference(self) -> str:
        """The number the sender is given on the confirmation page, e.g. #0042."""
        return f"#{self.pk:04d}"

    @property
    def channel(self) -> str:
        """The reason as the console shows it: CH1, CH2 or CH3."""
        return f"CH{self.Reason.values.index(self.reason) + 1}"

    @property
    def first_name(self) -> str:
        return self.name.split()[0] if self.name.split() else "there"
