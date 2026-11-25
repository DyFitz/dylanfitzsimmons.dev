import time
from datetime import timedelta
from typing import Any

import pytest
from django.core import mail, signing
from django.core.mail import EmailMessage
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone
from pytest_django import Settings
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects

from apps.contact import spam
from apps.contact.models import Message
from apps.contact.views import SESSION_KEY

pytestmark = pytest.mark.django_db

MESSAGE = (
    "Hi Dylan, we have a graduate developer role on our trading systems team. "
    "Would you be up for a chat next week?"
)


def served(seconds_ago: float = 10) -> str:
    return signing.dumps(time.time() - seconds_ago, salt=spam.SERVED_SALT)


def form_data(**overrides: Any) -> dict[str, Any]:
    return {
        "name": "Alex Morgan",
        "email": "alex@example.com",
        "reason": "job",
        "body": MESSAGE,
        "website": "",
        "served": served(),
        **overrides,
    }


def send(client: Client, **overrides: Any) -> Any:
    return client.post(reverse("contact:page"), form_data(**overrides))


def sent_page(client: Client) -> Any:
    send(client)
    return client.get(reverse("contact:sent"))


# ---------------------------------------------------------------- the form


def test_contact_page_shows_the_form(client: Client) -> None:
    response = client.get(reverse("contact:page"))

    assert response.status_code == 200
    assertContains(response, 'method="post"')
    assertContains(response, "csrfmiddlewaretoken")
    assertContains(response, 'name="served"')
    assertContains(response, "Job opportunity")
    assertContains(response, "Project or freelance")
    assertContains(response, "Something else")
    assertContains(response, 'id="privacy"')


def test_the_globe_has_a_still_version(client: Client) -> None:
    for response in (client.get(reverse("contact:page")), sent_page(client)):
        assertContains(response, 'class="still" src="/static/img/globe.svg"')
        assertContains(response, 'class="live" data-uplink-globe')


def test_no_email_address_on_the_page(client: Client) -> None:
    response = client.get(reverse("contact:page"))

    assertNotContains(response, "@dylanfitzsimmons.dev")
    assertNotContains(response, "hotmail")
    assertNotContains(response, "mailto:")


def test_the_honeypot_is_on_the_page_but_out_of_the_way(client: Client) -> None:
    response = client.get(reverse("contact:page"))

    assertContains(response, 'class="honeypot" aria-hidden="true"')
    assertContains(response, f'name="{spam.HONEYPOT_FIELD}"')
    assertContains(response, 'tabindex="-1"')


# ---------------------------------------------------------------- sending


def test_a_message_is_saved_emailed_and_confirmed(client: Client, settings: Settings) -> None:
    response = send(client)

    assertRedirects(response, reverse("contact:sent"))
    message = Message.objects.get()
    assert message.name == "Alex Morgan"
    assert message.email == "alex@example.com"
    assert message.reason == Message.Reason.JOB
    assert message.body == MESSAGE
    assert message.emailed
    assert message.sender_hash

    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.to == [settings.CONTACT_EMAIL]
    assert email.reply_to == ["Alex Morgan <alex@example.com>"]
    assert message.reference in email.subject
    assert MESSAGE in email.body


def test_the_confirmation_shows_the_message_going_out(client: Client) -> None:
    send(client)
    message = Message.objects.get()

    response = client.get(reverse("contact:sent"))

    assertContains(response, message.reference)
    assertContains(response, "Thanks, Alex.")
    assertContains(response, "0000  48 69 20 44 79 6c 61 6e")
    assertContains(response, "checksum 0x9DF6")
    assertContains(response, "62 more bytes")
    # The narrow one, for phones.
    assertContains(response, "48 69 20 44 79 6c 61 6e  |Hi Dylan|")
    assertContains(response, "… 78 more bytes")


def test_refreshing_the_confirmation_does_not_send_it_again(client: Client) -> None:
    send(client)

    client.get(reverse("contact:sent"))
    client.get(reverse("contact:sent"))

    assert Message.objects.count() == 1
    assert len(mail.outbox) == 1


def test_the_confirmation_is_not_cached(client: Client) -> None:
    send(client)

    response = client.get(reverse("contact:sent"))

    assert "no-store" in response["Cache-Control"]


def test_the_confirmation_is_only_for_the_sender(client: Client) -> None:
    send(client)

    assertRedirects(Client().get(reverse("contact:sent")), reverse("contact:page"))


def test_the_confirmation_without_a_message_goes_back_to_the_form(client: Client) -> None:
    session = client.session
    session[SESSION_KEY] = 999_999
    session.save()

    assertRedirects(client.get(reverse("contact:sent")), reverse("contact:page"))


def test_a_message_is_kept_even_if_the_email_fails(
    client: Client, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def fail(self: EmailMessage, fail_silently: bool = False) -> int:
        raise ConnectionRefusedError

    monkeypatch.setattr(EmailMessage, "send", fail)

    response = send(client)

    assertRedirects(response, reverse("contact:sent"))
    assert not Message.objects.get().emailed
    assert "Couldn't email contact message" in caplog.text


def test_old_messages_are_cleared_out_when_one_arrives(client: Client) -> None:
    old = Message.objects.create(
        name="Old",
        email="old@example.com",
        body="Hello",
        sent_at=timezone.now() - timedelta(days=400),
    )

    send(client)

    assert not Message.objects.filter(pk=old.pk).exists()
    assert Message.objects.count() == 1


# ---------------------------------------------------------------- mistakes


def test_a_missing_name_is_pointed_out_on_its_row(client: Client) -> None:
    response = send(client, name="")

    assert response.status_code == 200
    assertContains(response, "FROM · your name is missing")
    assertContains(response, 'aria-invalid="true"')
    assertContains(response, 'aria-describedby="id_name-error"')
    assertContains(response, 'id="id_name-error"')
    assert not Message.objects.exists()


def test_an_incomplete_email_address_is_pointed_out(client: Client) -> None:
    response = send(client, email="alex@")

    assertContains(response, "REPLY-TO · that address is incomplete")


def test_an_empty_message_is_pointed_out(client: Client) -> None:
    response = send(client, body="   ")

    assertContains(response, "MESSAGE · nothing to send yet")


def test_what_was_typed_is_kept_when_there_is_a_mistake(client: Client) -> None:
    response = send(client, name="")

    assertContains(response, MESSAGE)
    assertContains(response, 'value="alex@example.com"')


def test_a_name_cannot_contain_line_breaks(client: Client) -> None:
    response = send(client, name="Alex\r\nBcc: someone@example.com")

    assertContains(response, "a name can&#x27;t contain line breaks")
    assert not Message.objects.exists()


def test_messages_are_limited_to_2000_characters(client: Client) -> None:
    response = send(client, body="a" * 2001)

    assertContains(response, "that&#x27;s over 2,000 characters")


def test_line_breaks_count_as_one_character(client: Client) -> None:
    # 2,001 characters as sent, but the browser counts the \r\n as one.
    send(client, body="a" * 1000 + "\r\n" + "a" * 999)

    assert Message.objects.get().body == "a" * 1000 + "\n" + "a" * 999


# ---------------------------------------------------------------- spam


def test_a_filled_in_honeypot_looks_sent_but_is_thrown_away(client: Client) -> None:
    response = send(client, website="https://spam.example.com")

    assertRedirects(response, reverse("contact:sent"), target_status_code=302)
    assert not Message.objects.exists()
    assert not mail.outbox


def test_a_form_sent_back_too_quickly_is_turned_away(client: Client) -> None:
    response = send(client, served=served(seconds_ago=1))

    assertContains(response, "That was sent very quickly")
    assert not Message.objects.exists()


def test_a_tampered_timestamp_is_turned_away(client: Client) -> None:
    token = served()

    response = send(client, served=token[:-2] + "xx")

    assertContains(response, "Something went wrong with the form")
    assert not Message.objects.exists()


def test_a_missing_timestamp_is_turned_away(client: Client) -> None:
    response = send(client, served="")

    assertContains(response, "Something went wrong with the form")


def test_a_form_left_open_for_over_a_day_is_refreshed(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    token = served()
    later = time.time() + spam.MAX_SECONDS + 60
    monkeypatch.setattr(time, "time", lambda: later)

    response = send(client, served=token)

    assertContains(response, "This form was open for over a day")
    assertNotContains(response, f'value="{token}"')
    assert not Message.objects.exists()


def reach_the_limit(**fields) -> None:
    """Saves as many messages from the test client's address as the hourly limit allows."""
    sender = spam.sender_hash(RequestFactory().get("/"))
    for _ in range(spam.RATE_LIMIT):
        Message.objects.create(
            name="Alex", email="alex@example.com", body="Hello", sender_hash=sender, **fields
        )


def test_a_few_messages_an_hour_from_one_sender(client: Client) -> None:
    reach_the_limit()

    response = send(client)

    assertContains(response, "You&#x27;ve sent a few messages in the last hour")
    assert Message.objects.count() == spam.RATE_LIMIT


def test_messages_from_over_an_hour_ago_do_not_count_towards_the_limit(client: Client) -> None:
    reach_the_limit(sent_at=timezone.now() - timedelta(hours=2))

    assertRedirects(send(client), reverse("contact:sent"))


def test_the_limit_is_per_sender(client: Client) -> None:
    for _ in range(spam.RATE_LIMIT):
        Message.objects.create(
            name="Sam", email="sam@example.com", body="Hello", sender_hash="someone-else"
        )

    assertRedirects(send(client), reverse("contact:sent"))
