from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.contact.models import RETENTION, Message

pytestmark = pytest.mark.django_db


def make(**fields: object) -> Message:
    return Message.objects.create(
        **{"name": "Alex Morgan", "email": "alex@example.com", "body": "Hello", **fields}
    )


def test_reference_channel_and_first_name() -> None:
    message = make(reason=Message.Reason.PROJECT)

    assert message.reference == f"#{message.pk:04d}"
    assert message.channel == "CH2"
    assert message.first_name == "Alex"
    assert str(message) == f"{message.reference} from Alex Morgan"


def test_expired_is_older_than_the_retention_period() -> None:
    kept = make(sent_at=timezone.now() - RETENTION + timedelta(days=1))
    expired = make(sent_at=timezone.now() - RETENTION - timedelta(days=1))

    assert list(Message.objects.expired()) == [expired]
    assert kept not in Message.objects.expired()


def test_delete_old_messages_command() -> None:
    make(sent_at=timezone.now() - RETENTION - timedelta(days=1))
    make()
    out = StringIO()

    call_command("delete_old_messages", stdout=out)

    assert out.getvalue().strip() == "Deleted 1 message."
    assert Message.objects.count() == 1


def test_messages_can_be_read_but_not_changed_in_the_admin(admin_client: Client) -> None:
    message = make()

    changelist = admin_client.get(reverse("admin:contact_message_changelist"))
    detail = admin_client.get(reverse("admin:contact_message_change", args=[message.pk]))
    add = admin_client.get(reverse("admin:contact_message_add"))

    assert changelist.status_code == 200
    assert message.reference.encode() in changelist.content
    assert detail.status_code == 200
    assert b"Hello" in detail.content
    assert b'name="_save"' not in detail.content
    assert add.status_code == 403
